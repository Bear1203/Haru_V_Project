using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Haru_PYR : MonoBehaviour
{
    GameObject Sphere;
    private float x, y, z;
    // Start is called before the first frame update
    void Start()
    {
        Sphere = GameObject.Find("Sphere");
    }

    // Update is called once per frame
    void Update()
    {
        x = -HaruGlobalConnectValue.pitch;
        y = -HaruGlobalConnectValue.yaw;
        z = 0;

        x += Time.deltaTime * 10;
        y += Time.deltaTime * 10;
        z += Time.deltaTime * 10;
        Sphere.transform.rotation = Quaternion.Euler(x + 50, y, z);
    }
}
