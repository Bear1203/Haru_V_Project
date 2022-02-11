using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class HaruExpression : MonoBehaviour
{
    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    public void click1(){
        HaruGlobalConnectValue.click_expression = 3;
    }

    public void click2(){
        HaruGlobalConnectValue.click_expression = 1;
    }

    public void click3(){
        HaruGlobalConnectValue.click_expression = 7;
    }

    public void click4(){
        HaruGlobalConnectValue.click_expression = 5;
    }

    public void click5(){
        HaruGlobalConnectValue.click_expression = 6;
    }

}
