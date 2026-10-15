using UnityEngine;

public sealed class ProductionTwinRuntime : MonoBehaviour
{
    public Transform xAxis;
    public Transform yAxis;
    public Transform zAxis;
    public Transform pusher;

    // Millimetres relative to the estimated home pose in parts.csv.
    public float xMm;
    public float yMm;
    public float lowerMm;
    public float pusherMm;
    public bool ps1Detected;
    public bool ps2Detected;
    public int ps1PulseCount;
    public int ps2PulseCount;

    public void SetPoseMm(float x, float y, float lower, float push)
    {
        xMm = x;
        yMm = y;
        lowerMm = lower;
        pusherMm = push;
        ApplyPose();
    }

    public void ApplyPose()
    {
        if (xAxis != null) xAxis.localPosition = new Vector3(xMm / 1000f, 0f, 0f);
        if (yAxis != null) yAxis.localPosition = new Vector3(0f, 0f, yMm / 1000f);
        if (zAxis != null) zAxis.localPosition = new Vector3(0f, -lowerMm / 1000f, 0f);
        if (pusher != null) pusher.localPosition = new Vector3(0f, 0f, pusherMm / 1000f);
    }

    private void OnValidate() => ApplyPose();
}
