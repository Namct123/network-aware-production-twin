using System.Collections;
using UnityEngine;

// Visual demonstration only. The PLC remains the authority for real motion.
public sealed class ProductionTwinDemo : MonoBehaviour
{
    public ProductionTwinRuntime twin;
    public bool playOnStart = true;
    public float beltSpeedMmPerSecond = 160f;
    public float axisSpeedMmPerSecond = 280f;
    public float cylinderSpeedMmPerSecond = 140f;

    private readonly Transform[] frontMarks = new Transform[5];
    private readonly Transform[] longMarks = new Transform[5];
    private GameObject product;
    private bool carrying;
    private bool ps1WasDetected;
    private bool ps2WasDetected;

    private IEnumerator Start()
    {
        if (!playOnStart || twin == null) yield break;
        CreateBeltMarks();
        twin.SetPoseMm(0f, 0f, 0f, 0f);
        for (int bin = 0; bin < 6; bin++)
            yield return Cycle(bin);
    }

    private void Update()
    {
        if (!playOnStart || twin == null) return;
        float travel = Time.time * Mathf.Max(1f, beltSpeedMmPerSecond) / 1000f;
        for (int i = 0; i < frontMarks.Length; i++)
        {
            if (frontMarks[i] == null) continue;
            frontMarks[i].localPosition = new Vector3(
                .255f - Mathf.Repeat(travel + i * .118f, .59f), .050f, -.325f);
            longMarks[i].localPosition = new Vector3(
                -.180f, .050f, -.265f + Mathf.Repeat(travel + i * .098f, .49f));
        }
        if (carrying && product != null)
            product.transform.position = new Vector3(
                -.180f + twin.xMm / 1000f,
                .116f - twin.lowerMm / 1000f,
                .120f + twin.yMm / 1000f);
        // The two diffuse sensors look across the long belt at y=-65 and 170 mm.
        twin.ps1Detected = SeesProduct(-.065f);
        twin.ps2Detected = SeesProduct(.170f);
        if (twin.ps1Detected && !ps1WasDetected) twin.ps1PulseCount++;
        if (twin.ps2Detected && !ps2WasDetected) twin.ps2PulseCount++;
        ps1WasDetected = twin.ps1Detected;
        ps2WasDetected = twin.ps2Detected;
    }

    private IEnumerator Cycle(int bin)
    {
        product = GameObject.CreatePrimitive(PrimitiveType.Cube);
        product.name = "Demo product " + (bin + 1);
        product.transform.SetParent(transform, false);
        product.transform.localScale = Vector3.one * .022f;
        Destroy(product.GetComponent<Collider>());
        var material = new Material(Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard"));
        material.color = bin % 2 == 0 ? new Color(.77f, .53f, .27f) : new Color(.35f, .57f, .78f);
        product.GetComponent<Renderer>().material = material;
        product.transform.localPosition = new Vector3(.220f, .060f, -.325f);

        yield return MoveProduct(new Vector3(-.180f, .060f, -.325f));
        yield return PushProduct();
        yield return MovePose(0f, 0f, 0f, 0f, cylinderSpeedMmPerSecond);
        yield return MoveProduct(new Vector3(-.180f, .060f, .170f));
        yield return MovePose(0f, 50f, 0f, 0f, axisSpeedMmPerSecond);
        yield return MovePose(0f, 50f, 56f, 0f, cylinderSpeedMmPerSecond);
        carrying = true;
        yield return MovePose(0f, 50f, 0f, 0f, cylinderSpeedMmPerSecond);

        int row = bin / 2, column = bin % 2;
        float x = column == 0 ? 80f : 195f;
        float y = 75f + row * 115f;
        yield return MovePose(x + 180f, y - 120f, 0f, 0f, axisSpeedMmPerSecond);
        yield return MovePose(x + 180f, y - 120f, 75f, 0f, cylinderSpeedMmPerSecond);
        carrying = false;
        yield return MovePose(x + 180f, y - 120f, 0f, 0f, cylinderSpeedMmPerSecond);
        product = null;
        yield return MovePose(0f, 0f, 0f, 0f, axisSpeedMmPerSecond);
    }

    private IEnumerator MoveProduct(Vector3 target)
    {
        Vector3 start = product.transform.localPosition;
        float duration = Vector3.Distance(start, target) * 1000f / Mathf.Max(1f, beltSpeedMmPerSecond);
        for (float t = 0f; t < duration; t += Time.deltaTime)
        {
            product.transform.localPosition = Vector3.Lerp(start, target, t / duration);
            yield return null;
        }
        product.transform.localPosition = target;
    }

    private IEnumerator PushProduct()
    {
        const float stroke = 110f;
        float duration = stroke / Mathf.Max(1f, cylinderSpeedMmPerSecond);
        for (float t = 0f; t < duration; t += Time.deltaTime)
        {
            float push = Mathf.Lerp(0f, stroke, t / duration);
            twin.SetPoseMm(0f, 0f, 0f, push);
            product.transform.localPosition = new Vector3(-.180f, .060f,
                (-325f + Mathf.Max(0f, push - 49f) * 1.2f) / 1000f);
            yield return null;
        }
        twin.SetPoseMm(0f, 0f, 0f, stroke);
        product.transform.localPosition = new Vector3(-.180f, .060f, -.252f);
    }

    private IEnumerator MovePose(float x, float y, float lower, float push, float speed)
    {
        Vector4 start = new Vector4(twin.xMm, twin.yMm, twin.lowerMm, twin.pusherMm);
        Vector4 end = new Vector4(x, y, lower, push);
        float duration = Mathf.Max(Mathf.Abs(x - start.x), Mathf.Abs(y - start.y),
            Mathf.Abs(lower - start.z), Mathf.Abs(push - start.w)) / Mathf.Max(1f, speed);
        for (float t = 0f; t < duration; t += Time.deltaTime)
        {
            Vector4 p = Vector4.Lerp(start, end, t / duration);
            twin.SetPoseMm(p.x, p.y, p.z, p.w);
            yield return null;
        }
        twin.SetPoseMm(x, y, lower, push);
    }

    private void CreateBeltMarks()
    {
        var marks = new GameObject("Belt motion indicators").transform;
        marks.SetParent(transform, false);
        var material = new Material(Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard"));
        material.color = new Color(.04f, .23f, .12f);
        for (int i = 0; i < frontMarks.Length; i++)
        {
            frontMarks[i] = Mark(marks, "Front belt mark", new Vector3(.003f, .001f, .060f), material);
            longMarks[i] = Mark(marks, "Long belt mark", new Vector3(.060f, .001f, .003f), material);
        }
    }

    private static Transform Mark(Transform parent, string name, Vector3 scale, Material material)
    {
        var mark = GameObject.CreatePrimitive(PrimitiveType.Cube);
        mark.name = name;
        mark.transform.SetParent(parent, false);
        mark.transform.localScale = scale;
        Destroy(mark.GetComponent<Collider>());
        mark.GetComponent<Renderer>().sharedMaterial = material;
        return mark.transform;
    }

    private bool SeesProduct(float sensorY)
    {
        return product != null && !carrying &&
               Mathf.Abs(product.transform.localPosition.x + .180f) < .020f &&
               Mathf.Abs(product.transform.localPosition.z - sensorY) < .012f;
    }
}
