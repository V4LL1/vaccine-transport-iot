// --- PARÂMETROS GERAIS (Medidas em mm) ---
largura_proto = 58;      // Largura da protoboard (+ folga leve)
comprimento_proto = 86;  // Comprimento da protoboard (+ folga leve)
altura_interna = 45;     // Altura interna da caixa (ESP32 + fios)

espessura_parede = 2.0;
raio_canto = 3;

// --- PARÂMETROS DOS BURACOS ---

// 1. Configuração do USB (Lateral MENOR - "Frente")
largura_usb = 14;         // Largura do buraco para o conector USB
altura_usb = 10;          // Altura do buraco para o conector USB
altura_do_chao_usb = 6;   // ⚠️ ALTURA DO USB ATÉ O CHÃO INTERNO DA CAIXA (AJUSTE!)

// 2. Configuração do DHT22 (Lateral MAIOR - "Lado Direito")
largura_dht = 18;         // Largura do buraco para o corpo do DHT22 ou seus fios
altura_dht = 26;          // Altura do buraco para o DHT22
distancia_canto_dht = 15; // Distância do canto esquerdo da parede até o buraco do DHT22
altura_do_chao_dht = 10;  // ⚠️ ALTURA DO DHT22 ATÉ O CHÃO INTERNO DA CAIXA (AJUSTE!)

// --- RENDERIZAÇÃO ---

$fn = 60; // Qualidade da curva

dim_x = comprimento_proto + (espessura_parede * 2);
dim_y = largura_proto + (espessura_parede * 2);
dim_z = altura_interna + espessura_parede;

module caixa_arredondada(x, y, z, r) {
    hull() {
        translate([r, r, 0]) cylinder(h=z, r=r);
        translate([x-r, r, 0]) cylinder(h=z, r=r);
        translate([x-r, y-r, 0]) cylinder(h=z, r=r);
        translate([r, y-r, 0]) cylinder(h=z, r=r);
    }
}

difference() {
    // 1. O Bloco Principal
    caixa_arredondada(dim_x, dim_y, dim_z, raio_canto);
    
    // 2. O Oco Interno
    translate([espessura_parede, espessura_parede, espessura_parede])
        caixa_arredondada(comprimento_proto, largura_proto, dim_z + 1, raio_canto/2);
        
    // --- CORTES (Buracos) ---
    
    // A. Buraco USB (Na face frontal - Y=0)
    // Centralizado no eixo X da parede
    translate([(dim_x/2) - (largura_usb/2), -1, espessura_parede + altura_do_chao_usb])
        cube([largura_usb, espessura_parede + 2, altura_usb]);

    // B. Buraco DHT22 (Na lateral direita - X=dim_x)
    // Distância do canto "inferior" da parede Y=0
    translate([dim_x - espessura_parede -2, distancia_canto_dht, espessura_parede + altura_do_chao_dht])
        rotate([0, 90, 0]) // Rotaciona para cortar na face certa
        cube([espessura_parede + 2, altura_dht, largura_dht]);
        
    // C. Ventilação na tampa
    for (i = [10 : 15 : dim_x-10]) {
        for (j = [10 : 15 : dim_y-10]) {
            translate([i, j, dim_z - espessura_parede/2])
                sphere(r=1.5);
        }
    }
}

// --- TAMPA ---
// Renderizada ao lado da caixa para imprimir junto
translate([0, dim_y + 15, 0]) {
    difference() {
        caixa_arredondada(dim_x, dim_y, 2, raio_canto);
        // Rebaixo da tampa para encaixe
        translate([espessura_parede + 0.2, espessura_parede + 0.2, -1]) 
            caixa_arredondada(comprimento_proto - 0.4, largura_proto - 0.4, 2, raio_canto/2);
    }
    // Borda de encaixe que se projeta na caixa
    translate([espessura_parede + 0.2, espessura_parede + 0.2, 2])
        difference() {
            caixa_arredondada(comprimento_proto - 0.4, largura_proto - 0.4, 3, raio_canto/2);
            translate([1, 1, -1])
                caixa_arredondada(comprimento_proto - 2.4, largura_proto - 2.4, 5, raio_canto/2);
        }
}