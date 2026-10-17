#version 150

// Lo que brilla (sol, auroras, ojos, antorchas): se queda lo que pasa del umbral, a un cuarto de tamano.
uniform sampler2D Sampler0;
uniform vec2 Texel;
uniform float Umbral;

in vec2 texCoord;
out vec4 fragColor;

void main() {
    vec3 c = texture(Sampler0, texCoord + Texel * vec2(-1.0, -1.0)).rgb
           + texture(Sampler0, texCoord + Texel * vec2(1.0, -1.0)).rgb
           + texture(Sampler0, texCoord + Texel * vec2(-1.0, 1.0)).rgb
           + texture(Sampler0, texCoord + Texel * vec2(1.0, 1.0)).rgb;
    c *= 0.25;
    float lum = max(c.r, max(c.g, c.b));
    float k = smoothstep(Umbral, Umbral + 0.25, lum);
    fragColor = vec4(c * k, 1.0);
}
