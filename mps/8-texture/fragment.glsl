#version 300 es
precision highp float;
uniform vec4 color;
out vec4 fragColor;
in vec4 vnormal;

uniform vec3 lightdir;
uniform vec4 lightcolor;
uniform vec3 halfway;

void main() {

    vec3 n = normalize(vnormal.xyz);

    float lambert = max(dot(n, lightdir), 0.f) * (1.f - lightcolor.a);

    float blinn = pow(max(dot(n, halfway), 0.f), 150.f);

    vec3 finalColor = (lightcolor.rgb * lambert) +
        ((lightcolor.rgb * blinn) * 3.f);

    fragColor = vec4(finalColor, 1.f);

}