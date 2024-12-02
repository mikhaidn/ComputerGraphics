#version 300 es
precision highp float;
uniform vec4 color;
out vec4 fragColor;
in vec3 vnormal;

uniform vec3 lightdir;
uniform vec3 halfway;
uniform vec3 ballcolor;

void main() {

    vec3 n = normalize(vnormal.xyz);

    float lambert = max(dot(n, lightdir), 0.f);

    float blinn = pow(max(dot(n, halfway), 0.f), 150.f);

    vec3 finalColor = (ballcolor * lambert) +
        ((ballcolor * blinn) * 3.f);

    fragColor = vec4(finalColor, 1.f);

}