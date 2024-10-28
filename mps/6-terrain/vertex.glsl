#version 300 es
layout(location=0)in vec4 position;
layout(location=1)in vec4 color;
out vec4 color2;
uniform mat4 m;
uniform mat4 v;
uniform mat4 p;
void main(){
    gl_Position=p*v*m*position;
    color2=color;
}