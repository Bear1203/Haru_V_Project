using System.Collections;
using System.Collections.Generic;
using UnityEngine;


/// <summary>
/// Forces a <see cref="GameObject"/> to face a camera.
/// </summary>
public class Haru_boarder : MonoBehaviour
{
    /// <summary>
    /// Camera to face.
    /// </summary>
    [SerializeField] public Camera CameraToFace;

    #region Unity Event Handling

    /// <summary>
    /// Called by Unity. Updates facing.
    /// </summary>
    private void Update()
    {
        if (CameraToFace.orthographic)
        {
            transform.LookAt(transform.position - CameraToFace.transform.forward, CameraToFace.transform.up);
        }
        else
        {
            transform.LookAt(CameraToFace.transform.position, CameraToFace.transform.up);
        }
    }

    #endregion
}