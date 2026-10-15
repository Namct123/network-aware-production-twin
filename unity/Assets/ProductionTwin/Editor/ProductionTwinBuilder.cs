using System;
using System.Globalization;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

public static class ProductionTwinBuilder
{
    private const string Folder = "Assets/ProductionTwin";

    [MenuItem("Tools/Production Twin/Build Scene")]
    public static void Build()
    {
        string csv = Path.Combine(Application.dataPath, "ProductionTwin/parts.csv");
        if (!File.Exists(csv)) throw new FileNotFoundException("Missing parts.csv", csv);
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var root = new GameObject("Production Twin V4");
        var fixedParts = Child(root.transform, "Static");
        var xAxis = Child(root.transform, "X axis - mm from home");
        var yAxis = Child(xAxis, "Y axis - mm from home");
        var zAxis = Child(yAxis, "A2 down - mm from home");
        var pusher = Child(root.transform, "A1 pusher - mm from home");
        var materialFolder = Folder + "/Materials";
        if (!AssetDatabase.IsValidFolder(materialFolder))
            AssetDatabase.CreateFolder(Folder, "Materials");

        int count = 0;
        string[] lines = File.ReadAllLines(csv);
        for (int i = 1; i < lines.Length; i++)
        {
            string line = lines[i];
            if (string.IsNullOrWhiteSpace(line)) continue;
            string[] p = line.Split(',');
            if (p.Length != 11) throw new FormatException("Invalid parts.csv row: " + line);
            string name = p[0], group = p[1];
            bool cylinder = p[2] == "cylinder", alongX = p[9] == "1", alongY = p[10] == "1";
            float px = Mm(p[3]), py = Mm(p[4]), pz = Mm(p[5]);
            float sx = Mm(p[6]), sy = Mm(p[7]), sz = Mm(p[8]);
            Transform parent = group == "X" ? xAxis : group == "Y" ? yAxis :
                               group == "Z" ? zAxis : group == "Pusher" ? pusher : fixedParts;
            var part = GameObject.CreatePrimitive(cylinder ? PrimitiveType.Cylinder : PrimitiveType.Cube);
            part.name = name;
            part.transform.SetParent(parent, false);
            if (cylinder)
            {
                part.transform.localPosition = alongX
                    ? new Vector3(px + sz / 2f, pz, py)
                    : alongY ? new Vector3(px, pz, py + sz / 2f)
                    : new Vector3(px, pz + sz / 2f, py);
                part.transform.localScale = new Vector3(sx, sz / 2f, sy);
                if (alongX) part.transform.localRotation = Quaternion.Euler(0f, 0f, 90f);
                if (alongY) part.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
            }
            else
            {
                part.transform.localPosition = new Vector3(px, pz + sz / 2f, py);
                part.transform.localScale = new Vector3(sx, sz, sy);
            }
            UnityEngine.Object.DestroyImmediate(part.GetComponent<Collider>());
            part.GetComponent<Renderer>().sharedMaterial = MaterialFor(name, materialFolder);
            count++;
        }

        var controller = root.AddComponent<ProductionTwinRuntime>();
        controller.xAxis = xAxis;
        controller.yAxis = yAxis;
        controller.zAxis = zAxis;
        controller.pusher = pusher;
        root.AddComponent<ProductionTwinDemo>().twin = controller;
        var light = new GameObject("Sun").AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.8f;
        light.color = new Color(1f, .96f, .89f);
        light.shadows = LightShadows.Soft;
        light.shadowStrength = .7f;
        light.transform.rotation = Quaternion.Euler(50f, -35f, 0f);
        RenderSettings.ambientMode = AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(.42f, .48f, .57f);
        var camera = new GameObject("Overview camera").AddComponent<Camera>();
        camera.orthographic = true;
        camera.orthographicSize = 0.68f;
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(.055f, .075f, .105f);
        camera.allowHDR = true;
        camera.allowMSAA = true;
        camera.transform.position = new Vector3(0.85f, 1.35f, -0.85f);
        camera.transform.LookAt(new Vector3(0f, 0.12f, 0f));
        EditorSceneManager.SaveScene(SceneManager.GetActiveScene(), Folder + "/ProductionTwin.unity");
        Debug.Log("Production Twin V4: built " + count + " parts. Dimensions are estimates.");
    }

    private static Transform Child(Transform parent, string name)
    {
        var child = new GameObject(name).transform;
        child.SetParent(parent, false);
        return child;
    }

    private static float Mm(string value) =>
        float.Parse(value, CultureInfo.InvariantCulture) / 1000f;

    private static Material MaterialFor(string name, string folder)
    {
        string key = name.Contains("green belt") ? "Belt" :
                     name.StartsWith("bin ") ? "Bins" :
                     name.Contains("optical face") ? "Black" :
                     name.StartsWith("PS") ? "Sensor" :
                     name == "button Start" ? "StartButton" :
                     name == "button Reset" ? "ResetButton" :
                     name.StartsWith("button station") ? "WhitePlastic" :
                     name.StartsWith("button ") ? "StopButtons" :
                     name.StartsWith("PLC") || name.StartsWith("motor ") ? "DarkHousing" :
                     name.StartsWith("base board") ? "Base" :
                     name.Contains("vacuum cup") || name.Contains("coil") || name.Contains("spring cap") ? "Black" :
                     name.Contains("collet") || name.Contains("manual button") ? "BluePlastic" :
                     name.Contains("rod") || name.Contains("roller") ? "Steel" : "Aluminum";
        string path = folder + "/" + key + ".mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material != null) return material;
        var shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
        if (shader == null) throw new InvalidOperationException("No compatible Lit shader");
        material = new Material(shader);
        material.color = key == "Belt" ? new Color(.094f, .490f, .255f) :
                         key == "Bins" ? new Color(.871f, .835f, .910f) :
                         key == "Sensor" ? new Color(.937f, .718f, .169f) :
                         key == "StartButton" ? new Color(.10f, .69f, .24f) :
                         key == "ResetButton" ? new Color(.91f, .67f, .12f) :
                         key == "StopButtons" ? new Color(.80f, .21f, .20f) :
                         key == "WhitePlastic" ? new Color(.89f, .89f, .87f) :
                         key == "DarkHousing" ? new Color(.216f, .251f, .290f) :
                         key == "Base" ? new Color(.192f, .208f, .224f) :
                         key == "Black" ? new Color(.141f, .153f, .169f) :
                         key == "BluePlastic" ? new Color(.161f, .435f, .761f) :
                         key == "Steel" ? new Color(.490f, .533f, .573f) :
                         new Color(.710f, .737f, .761f);
        if (material.HasProperty("_Metallic"))
            material.SetFloat("_Metallic", key == "Aluminum" || key == "Steel" ? .65f : 0f);
        if (material.HasProperty("_Smoothness"))
            material.SetFloat("_Smoothness", key == "Aluminum" || key == "Steel" ? .38f : .12f);
        AssetDatabase.CreateAsset(material, path);
        return material;
    }
}
