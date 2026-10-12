#version 150

// Desenfoque gaussiano en una direccion (se pasa dos veces: de lado y de arriba a abajo).
uniform sampler2D Sampler0;
uniform vec2 Direccion;

in vec2 texCoord;
out vec4 fragColor;

void main() {
    float pesos[5] = float[](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);
    vec3 c = texture(Sampler0, texCoord).rgb * pesos[0];
    for (int i = 1; i < 5; i++) {
        c += texture(Sampler0, texCoord + Direccion * float(i) * 1.6).rgb * pesos[i];
        c += texture(Sampler0, texCoord - Direccion * float(i) * 1.6).rgb * pesos[i];
    }
    fragColor = vec4(c, 1.0);
}
