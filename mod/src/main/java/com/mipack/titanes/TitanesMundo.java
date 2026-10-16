package com.mipack.titanes;

import com.mipack.Mipack;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Los titanes de un mundo: siempre estan, aunque nadie los vea. Cada uno tiene su registro (tipo, casa, donde va, que
 * hace y su camino). Si hay jugadores cerca, el titan aparece como entidad y se mueve solo; si se alejan todos, la
 * entidad se quita y el registro sigue el camino de forma virtual (avanza a su paso sobre el mapa del terreno y
 * escoge lo siguiente de su agenda), asi cuando alguien vuelve lo encuentra en otro lado. Se guarda con el mundo.
 */
public final class TitanesMundo extends SavedData {
    private static final String NOMBRE = "mipack_titanes";
    private static final double APARECE = 160, SE_QUITA = 240;

    public static final class Registro {
        public int id;
        public String tipo;
        public Vec3 casa, pos;
        public float giro;
        public UUID uuid;
        public List<Vec3> camino = new ArrayList<>();
        public int indice, espera;
        public TipoTitan.Actividad act;
    }

    private final List<Registro> registros = new ArrayList<>();
    private int siguienteId = 1;
    private int planesEsteTick;

    public static TitanesMundo de(ServerLevel nivel) {
        return nivel.getDataStorage().computeIfAbsent(TitanesMundo::cargar, TitanesMundo::new, NOMBRE);
    }

    public List<Registro> registros() {
        return this.registros;
    }

    public Registro registro(int id) {
        for (Registro r : this.registros)
            if (r.id == id)
                return r;
        return null;
    }

    public Registro crear(ServerLevel nivel, TipoTitan tipo, Vec3 pos, float giro) {
        Registro r = new Registro();
        r.id = this.siguienteId++;
        r.tipo = tipo.id();
        r.casa = pos;
        r.pos = pos;
        r.giro = giro;
        this.registros.add(r);
        this.setDirty();
        aparecer(nivel, r);
        return r;
    }

    public boolean quitar(ServerLevel nivel, int id) {
        Registro r = registro(id);
        if (r == null)
            return false;
        Titan t = entidad(nivel, r);
        if (t != null)
            t.discard();
        this.registros.remove(r);
        this.setDirty();
        return true;
    }

    public Titan entidad(ServerLevel nivel, Registro r) {
        if (r.uuid == null)
            return null;
        Entity e = nivel.getEntity(r.uuid);
        return e instanceof Titan t && t.isAlive() ? t : null;
    }

    /** Cada tick del mundo: cada titan se revisa una vez por segundo (repartidos entre los ticks). */
    public void tick(ServerLevel nivel) {
        this.planesEsteTick = 0;
        long t = nivel.getGameTime();
        for (Registro r : new ArrayList<>(this.registros)) {
            if ((t + r.id) % 20 != 0)
                continue;
            TipoTitan tipo = Titanes.tipo(r.tipo);
            if (tipo == null)
                continue;
            Titan e = entidad(nivel, r);
            if (e != null) {
                r.pos = e.position();
                r.giro = e.getYRot();
                r.camino = new ArrayList<>(e.camino());
                r.indice = e.indice();
                r.act = e.actividad();
                this.setDirty();
                if (!hayJugador(nivel, r.pos, SE_QUITA)) {
                    e.discard();
                    r.uuid = null;
                }
                continue;
            }
            virtual(nivel, tipo, r);
            if (hayJugador(nivel, r.pos, APARECE) && nivel.isPositionEntityTicking(BlockPos.containing(r.pos)))
                aparecer(nivel, r);
        }
    }

    private static boolean hayJugador(ServerLevel nivel, Vec3 p, double radio) {
        for (Player j : nivel.players())
            if (!j.isSpectator() && j.position().distanceToSqr(p.x, j.getY(), p.z) < radio * radio)
                return true;
        return false;
    }

    private void aparecer(ServerLevel nivel, Registro r) {
        TipoTitan tipo = Titanes.tipo(r.tipo);
        if (tipo == null || !nivel.isPositionEntityTicking(BlockPos.containing(r.pos)))
            return;
        Titan t = Titanes.entidad(r.tipo).create(nivel);
        if (t == null)
            return;
        t.moveTo(r.pos.x, r.pos.y, r.pos.z, r.giro, 0f);
        t.ligar(r.id, r.casa, r.camino, r.indice, r.act);
        double y = t.alturaObjetivo(r.pos.x, r.pos.z);
        t.setPos(r.pos.x, y, r.pos.z);
        nivel.addFreshEntity(t);
        r.uuid = t.getUUID();
        r.pos = t.position();
        this.setDirty();
    }

    /** Un segundo de vida sin entidad: avanza por el camino, espera haciendo lo suyo o escoge lo siguiente. */
    private void virtual(ServerLevel nivel, TipoTitan tipo, Registro r) {
        Terreno terreno = Terreno.de(nivel);
        if (r.indice < r.camino.size()) {
            double queda = tipo.velocidad() * 20;
            while (queda > 0 && r.indice < r.camino.size()) {
                Vec3 w = r.camino.get(r.indice);
                Vec3 d = new Vec3(w.x - r.pos.x, 0, w.z - r.pos.z);
                double dist = d.length();
                if (dist <= queda) {
                    r.pos = new Vec3(w.x, r.pos.y, w.z);
                    r.indice++;
                    queda -= dist;
                } else {
                    r.pos = r.pos.add(d.scale(queda / dist));
                    r.giro = (float) (Math.atan2(d.z, d.x) * 180 / Math.PI) - 90f;
                    queda = 0;
                }
            }
            Terreno.Celda c = terreno.celda(Terreno.celdaDe(r.pos.x), Terreno.celdaDe(r.pos.z));
            if (c != null)
                r.pos = new Vec3(r.pos.x, (tipo.perfil().modo() == Rutas.Modo.COPAS || tipo.perfil().modo() == Rutas.Modo.AIRE
                        ? c.copas() : tipo.perfil().modo() == Rutas.Modo.AGUA ? c.suelo() : c.fondo()) + tipo.altitud(), r.pos.z);
            if (r.indice >= r.camino.size()) {
                r.camino.clear();
                r.indice = 0;
                r.espera = r.act == null ? 200 : Math.max(40, r.act.ticks());
            }
            this.setDirty();
            return;
        }
        if (r.espera > 0) {
            r.espera -= 20;
            return;
        }
        if (this.planesEsteTick >= 1)
            return;                                               // un plan por tick para no trabar el servidor
        this.planesEsteTick++;
        r.act = tipo.agenda().siguiente(terreno, tipo, r.pos, r.casa, nivel.getDayTime(), nivel.random);
        if (r.act == null || r.act.lugar() == null) {
            r.espera = r.act == null ? 200 : r.act.ticks();
            return;
        }
        List<Vec3> c = Rutas.buscar(terreno, tipo.perfil(), r.pos, r.act.lugar(), 40000);
        if (c.isEmpty()) {
            r.espera = 200;
            if (Mipack.PRUEBA)
                Mipack.LOGGER.info("[Titanes] {} #{} (virtual) sin camino a {}", r.tipo, r.id, r.act.lugar());
            return;
        }
        r.camino = new ArrayList<>(c);
        r.indice = Math.min(1, c.size() - 1);
        this.setDirty();
    }

    // ------------------------------------------------------------------ guardar y cargar

    @Override
    public CompoundTag save(CompoundTag tag) {
        ListTag lista = new ListTag();
        for (Registro r : this.registros) {
            CompoundTag c = new CompoundTag();
            c.putInt("id", r.id);
            c.putString("tipo", r.tipo);
            vec(c, "casa", r.casa);
            vec(c, "pos", r.pos);
            c.putFloat("giro", r.giro);
            c.putInt("espera", r.espera);
            ListTag cam = new ListTag();
            for (int i = r.indice; i < r.camino.size(); i++) {
                CompoundTag p = new CompoundTag();
                vec(p, "p", r.camino.get(i));
                cam.add(p);
            }
            c.put("camino", cam);
            if (r.act != null) {
                c.putString("hacer", r.act.hacer().name());
                c.putInt("ticks", r.act.ticks());
                if (r.act.lugar() != null)
                    vec(c, "lugar", r.act.lugar());
            }
            lista.add(c);
        }
        tag.put("titanes", lista);
        tag.putInt("siguiente", this.siguienteId);
        return tag;
    }

    private static TitanesMundo cargar(CompoundTag tag) {
        TitanesMundo m = new TitanesMundo();
        m.siguienteId = Math.max(1, tag.getInt("siguiente"));
        for (Tag x : tag.getList("titanes", Tag.TAG_COMPOUND)) {
            CompoundTag c = (CompoundTag) x;
            Registro r = new Registro();
            r.id = c.getInt("id");
            r.tipo = c.getString("tipo");
            r.casa = vec(c, "casa");
            r.pos = vec(c, "pos");
            r.giro = c.getFloat("giro");
            r.espera = c.getInt("espera");
            for (Tag p : c.getList("camino", Tag.TAG_COMPOUND))
                r.camino.add(vec((CompoundTag) p, "p"));
            if (c.contains("hacer"))
                r.act = new TipoTitan.Actividad(c.contains("lugar") ? vec(c, "lugar") : null,
                        TipoTitan.Hacer.valueOf(c.getString("hacer")), c.getInt("ticks"));
            m.registros.add(r);
        }
        return m;
    }

    private static void vec(CompoundTag c, String k, Vec3 v) {
        c.putDouble(k + "x", v.x);
        c.putDouble(k + "y", v.y);
        c.putDouble(k + "z", v.z);
    }

    private static Vec3 vec(CompoundTag c, String k) {
        return new Vec3(c.getDouble(k + "x"), c.getDouble(k + "y"), c.getDouble(k + "z"));
    }
}
