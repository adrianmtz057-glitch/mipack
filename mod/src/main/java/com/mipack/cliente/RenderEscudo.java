package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.objetos.Escudo;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.model.ShieldModel;
import net.minecraft.client.model.geom.EntityModelSet;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderDispatcher;
import net.minecraft.client.renderer.entity.ItemRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/** Dibuja los escudos de Velkia con el modelo del escudo de Minecraft y su textura. */
public class RenderEscudo extends BlockEntityWithoutLevelRenderer {
    private final EntityModelSet modelos;
    private ShieldModel modelo;

    public RenderEscudo(BlockEntityRenderDispatcher d, EntityModelSet modelos) {
        super(d, modelos);
        this.modelos = modelos;
    }

    @Override
    public void renderByItem(ItemStack s, ItemDisplayContext contexto, PoseStack pose, MultiBufferSource buf, int luz, int capa) {
        if (!(s.getItem() instanceof Escudo e))
            return;
        if (modelo == null)
            modelo = new ShieldModel(modelos.bakeLayer(ModelLayers.SHIELD));
        ResourceLocation tex = new ResourceLocation(Mipack.MODID, "textures/entity/escudo/" + e.id() + ".png");
        pose.pushPose();
        pose.scale(1.0f, -1.0f, -1.0f);
        VertexConsumer vc = ItemRenderer.getFoilBufferDirect(buf, modelo.renderType(tex), true, s.hasFoil());
        modelo.renderToBuffer(pose, vc, luz, capa, 1.0f, 1.0f, 1.0f, 1.0f);
        pose.popPose();
    }
}
