using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Threading;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System;


public class HaruConnectTCP : MonoBehaviour
{
    Thread receiveThread;
    TcpClient client;
    TcpListener listener;
    int port = 1234;

    // Start is called before the first frame update
    void Start()
    {
        initTCP();
    }

    private void initTCP()
    {
        receiveThread = new Thread (new ThreadStart(ReceiveData));
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    private void ReceiveData()
    {
        try {           
            listener = new TcpListener(IPAddress.Parse("127.0.0.1"), port);
            listener.Start();
            Byte[] bytes = new Byte[1024];
            while (true) {
                using (client = listener.AcceptTcpClient()) {
                    using (NetworkStream stream = client.GetStream()) {
                        int length;
                        while ((length = stream.Read(bytes, 0, bytes.Length)) != 0) {
                            var incommingData = new byte[length];
                            Array.Copy(bytes, 0, incommingData, 0, length);
                            string clientMessage = Encoding.ASCII.GetString(incommingData);
                            string[] res = clientMessage.Split(' ');
                            HaruGlobalConnectValue.pitch = float.Parse(res[0]) * 12f;
                            HaruGlobalConnectValue.yaw = float.Parse(res[1]) * 4f;
                            // HaruGlobalConnectValue.roll = float.Parse(res[2]) * 0.5f;
                            HaruGlobalConnectValue.min_ear = (float.Parse(res[3])-0.2f) * 50f / 3f;
                            HaruGlobalConnectValue.mar = (float.Parse(res[4]) - 0.1f) * 5f;
                        }
                    }
                }
            }
        } catch(Exception e) {
            print (e.ToString());
        }
    }

}
