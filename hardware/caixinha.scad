// =============================================================
// Caixinha IoT — Transporte de Vacinas
// ESP32 DevKit V1 (cabeça para baixo na base)
// DHT22 (parede maior, branco para fora)
// GPS NEO-6M (interno)
// =============================================================
// EXPORTAR STL:
//   openscad -o caixa.stl caixinha.scad -D 'PART="caixa"'
//   openscad -o tampa.stl caixinha.scad -D 'PART="tampa"'
// =============================================================

PART = "caixa";  // "caixa" ou "tampa"

// ── Dimensões externas (mm) ──────────────────────────────────
L      = 170;  // comprimento (paredes MAIORES — DHT22)
W      = 90;   // largura     (paredes MENORES — USB e vents)
H_BOX  = 80;   // altura da caixa
H_LID  =  6;   // altura da tampa
T      =  2.5; // espessura da parede e fundo

// ── Encaixe tampa ────────────────────────────────────────────
LIP_H  = 3.0;  // profundidade do lip de encaixe
LIP_T  = 1.2;  // espessura do lip (folga de ~0.3mm para impressão)

// ── Buraco USB/alimentação (parede MENOR em Y=0) ─────────────
// ESP32 upside-down na base → USB aponta para a parede menor
// Micro-B plug real: ~11×7mm  →  2× margem: 22×14mm
USB_W  = 27;
USB_H  = 18;
USB_CZ = 0;  // começa na base (tipo porta)

// ── Buraco DHT22 (parede MAIOR em X=L) ──────────────────────
// Ligeiramente maior que o buraco USB (22×14mm)
DHT_W  = 29;   // eixo Y (largura da caixa)
DHT_H  = 21;   // eixo Z (altura da caixa)

// ── Furos de ventilação (parede MENOR em Y=W, oposta ao USB) ─
// 3 furos de 7mm ø, centrados na altura
VENT_D = 7;
VENT_Z = H_BOX / 2;

// =============================================================
if (PART == "caixa") caixa();
if (PART == "tampa") tampa();
// =============================================================

module caixa() {
    difference() {
        // ① Bloco externo sólido
        cube([L, W, H_BOX]);

        // ② Escavação interna (cria paredes + fundo, topo aberto)
        translate([T, T, T])
            cube([L - 2*T, W - 2*T, H_BOX]);

        // ③ Recorte USB — parede MENOR (X=0), centrado em Y, começa na base
        translate([-0.1,  W/2 - USB_W/2,  -0.1])
            cube([T + 0.2,  USB_W,  USB_H + 0.1]);

        // ④ Recorte DHT22 — parede MAIOR (Y=W), centrado em X e Z
        translate([L/2 - DHT_W/2,  W - T - 0.1,  H_BOX/2 - DHT_H/2])
            cube([DHT_W,  T + 0.2,  DHT_H]);

        // ⑤ Furos de ventilação — parede MENOR (X=L), oposta ao USB, 3 furos
        for (i = [0 : 2]) {
            translate([L - 0.1,  W * (0.25 + i * 0.25),  VENT_Z])
                rotate([0, 90, 0])
                    cylinder(d=VENT_D, h=T + 0.2, $fn=64);
        }
    }

    // ⑥ Lip interno para encaixar a tampa
    translate([T, T, H_BOX - LIP_H])
        difference() {
            cube([L - 2*T,  W - 2*T,  LIP_H]);
            translate([LIP_T,  LIP_T,  -0.1])
                cube([L - 2*T - 2*LIP_T,  W - 2*T - 2*LIP_T,  LIP_H + 0.2]);
        }
}

module tampa() {
    difference() {
        // Tampa sólida
        cube([L, W, H_LID]);
        // Recorte para encaixar no lip da caixa
        translate([T - LIP_T,  T - LIP_T,  -0.1])
            cube([L - 2*(T - LIP_T),  W - 2*(T - LIP_T),  LIP_H + 0.1]);
    }
}
