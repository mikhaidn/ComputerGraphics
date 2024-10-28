#version 300 es
precision highp float;
uniform vec4 color;
out vec4 fragColor;
in vec4 color2;
void main() {
    fragColor = color2;
}