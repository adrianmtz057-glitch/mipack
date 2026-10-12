package com.mipack.geo;

import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import net.minecraft.core.Direction;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.cache.object.GeoBone;
import software.bernie.geckolib.cache.object.GeoCube;
import software.bernie.geckolib.cache.object.GeoQuad;
import software.bernie.geckolib.cache.object.GeoVertex;
import software.bernie.geckolib.loading.json.raw.Bone;
import software.bernie.geckolib.loading.json.raw.Cube;
import software.bernie.geckolib.loading.json.raw.ModelProperties;
import software.bernie.geckolib.loading.json.raw.PolyMesh;
import software.bernie.geckolib.loading.object.BakedModelFactory;
import software.bernie.geckolib.loading.object.BoneStructure;
import software.bernie.geckolib.loading.object.GeometryTree;
import software.bernie.geckolib.util.RenderUtils;

import javax.annotation.Nullable;
import java.util.List;

/**
 * Arma los modelos de mipack como GeckoLib (cubos) y ademas sus MALLAS: GeckoLib lee el poly_mesh de cada hueso pero
 * no lo dibuja; aqui cada poligono se vuelve un cuadro (los triangulos repiten un vertice) de un "cubo" del hueso, y
 * se anima con el hueso como todo lo demas. Asi entran tal cual los modelos de malla del taller (Khaset, la Bruma...).
 * El poly_mesh lo escribe taller/geckolib.exportar_geo: posiciones con la x negada (como los cubos) en px, poligonos
 * de 4 vertices en orden contrario y UV en pixeles del atlas.
 */
public final class FabricaMallas implements BakedModelFactory {
    @Override
    public BakedGeoModel constructGeoModel(GeometryTree arbol) {
        List<GeoBone> huesos = new ObjectArrayList<>();
        for (BoneStructure b : arbol.topLevelBones().values())
            huesos.add(constructBone(b, arbol.properties(), null));
        return new BakedGeoModel(huesos, arbol.properties());
    }

    @Override
    public GeoBone constructBone(BoneStructure estructura, ModelProperties propiedades, @Nullable GeoBone padre) {
        Bone bone = estructura.self();
        GeoBone nuevo = new GeoBone(padre, bone.name(), bone.mirror(), bone.inflate(), bone.neverRender(), bone.reset());
        Vec3 rot = RenderUtils.arrayToVec(bone.rotation());
        Vec3 piv = RenderUtils.arrayToVec(bone.pivot());
        nuevo.updateRotation((float) Math.toRadians(-rot.x), (float) Math.toRadians(-rot.y), (float) Math.toRadians(rot.z));
        nuevo.updatePivot((float) -piv.x, (float) piv.y, (float) piv.z);
        for (Cube cubo : bone.cubes())
            nuevo.getCubes().add(constructCube(cubo, propiedades, nuevo));
        if (bone.polyMesh() != null && bone.polyMesh().polysUnion() != null)
            nuevo.getCubes().add(malla(bone.polyMesh(), propiedades));
        for (BoneStructure hijo : estructura.children().values())
            nuevo.getChildBones().add(constructBone(hijo, propiedades, nuevo));
        return nuevo;
    }

    @Override
    public GeoCube constructCube(Cube cubo, ModelProperties propiedades, GeoBone hueso) {
        return BakedModelFactory.DEFAULT_FACTORY.constructCube(cubo, propiedades, hueso);
    }

    /** Todos los poligonos de la malla de un hueso como un solo "cubo" de cuadros libres. */
    private static GeoCube malla(PolyMesh pm, ModelProperties propiedades) {
        double[] pos = pm.positions(), uv = pm.uvs();
        double[][][] polys = pm.polysUnion().union();
        boolean normalizadas = pm.normalizedUVs() == Boolean.TRUE;
        float tw = (float) propiedades.textureWidth(), th = (float) propiedades.textureHeight();
        GeoQuad[] cuadros = new GeoQuad[polys.length];
        for (int k = 0; k < polys.length; k++) {
            double[][] poli = polys[k];
            GeoVertex[] vs = new GeoVertex[4];
            for (int j = 0; j < 4; j++) {
                double[] e = poli[Math.min(poli.length, 4) - 1 - Math.min(j, poli.length - 1)];   // el orden de vuelta
                int p = (int) e[0], u = (int) e[2];
                float tu = (float) uv[2 * u], tv = (float) uv[2 * u + 1];
                if (!normalizadas) {
                    tu /= tw;
                    tv /= th;
                }
                vs[j] = new GeoVertex(new Vector3f((float) (-pos[3 * p] / 16.0), (float) (pos[3 * p + 1] / 16.0),
                        (float) (pos[3 * p + 2] / 16.0)), tu, tv);
            }
            Vector3f n = normal(vs);
            cuadros[k] = new GeoQuad(vs, n, Direction.getNearest(n.x, n.y, n.z));
        }
        return new GeoCube(cuadros, Vec3.ZERO, Vec3.ZERO, new Vec3(1, 1, 1), 0, false);
    }

    /** La normal hacia afuera (Newell: sirve igual para triangulos con un vertice repetido). */
    private static Vector3f normal(GeoVertex[] vs) {
        float nx = 0, ny = 0, nz = 0;
        for (int i = 0; i < vs.length; i++) {
            Vector3f a = vs[i].position(), b = vs[(i + 1) % vs.length].position();
            nx += (a.y - b.y) * (a.z + b.z);
            ny += (a.z - b.z) * (a.x + b.x);
            nz += (a.x - b.x) * (a.y + b.y);
        }
        Vector3f n = new Vector3f(nx, ny, nz);
        return n.lengthSquared() > 1e-12f ? n.normalize() : new Vector3f(0, 1, 0);
    }
}
