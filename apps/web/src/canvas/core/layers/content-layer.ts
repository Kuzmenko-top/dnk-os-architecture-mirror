/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/core/layers/content-layer.ts"
 * purpose: "Tier 2 Content Layer: high-performance rendering and management of user shapes, text, images, and custom nodes."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * --- END DNK-MRH-HEADER ---
 */

import Konva from 'konva';
import type { NodeProperties, LayerState } from '../../storage/types/canvas';

function safeDraw(layer: Konva.Layer): void {
  if (typeof window === 'undefined') {
    layer.draw();
  } else {
    layer.batchDraw();
  }
}

export type NodeEventHandler = (nodeId: string, event: Konva.KonvaEventObject<any>) => void;

export class ContentLayer {
  public readonly layer: Konva.Layer;
  private nodeMap = new Map<string, Konva.Node>();
  private onNodeClick?: NodeEventHandler;
  private onNodeDragMove?: NodeEventHandler;
  private onNodeDragEnd?: NodeEventHandler;
  private onNodeMouseEnter?: NodeEventHandler;
  private onNodeMouseLeave?: NodeEventHandler;

  constructor() {
    this.layer = new Konva.Layer({ id: 'dnk-tier-2-content', listening: true });
  }

  public setEventHandlers(handlers: {
    onClick?: NodeEventHandler;
    onDragMove?: NodeEventHandler;
    onDragEnd?: NodeEventHandler;
    onMouseEnter?: NodeEventHandler;
    onMouseLeave?: NodeEventHandler;
  }): void {
    this.onNodeClick = handlers.onClick;
    this.onNodeDragMove = handlers.onDragMove;
    this.onNodeDragEnd = handlers.onDragEnd;
    this.onNodeMouseEnter = handlers.onMouseEnter;
    this.onNodeMouseLeave = handlers.onMouseLeave;
  }

  public syncFromState(layers: LayerState[]): void {
    // Collect all active node IDs across all visible layers
    const activeIds = new Set<string>();

    for (const layerState of layers) {
      if (!layerState.visible) continue;

      for (const nodeProps of layerState.nodes) {
        activeIds.add(nodeProps.id);
        const existing = this.nodeMap.get(nodeProps.id);
        if (existing) {
          this.updateKonvaNode(existing, nodeProps);
        } else {
          const newNode = this.createKonvaNode(nodeProps);
          this.nodeMap.set(nodeProps.id, newNode);
          this.layer.add(newNode);
        }
      }
    }

    // Remove nodes that no longer exist in state
    for (const [id, konvaNode] of this.nodeMap.entries()) {
      if (!activeIds.has(id)) {
        konvaNode.destroy();
        this.nodeMap.delete(id);
      }
    }

    safeDraw(this.layer);
  }

  public addNode(nodeProps: NodeProperties): Konva.Node {
    const existing = this.nodeMap.get(nodeProps.id);
    if (existing) {
      existing.destroy();
    }
    const node = this.createKonvaNode(nodeProps);
    this.nodeMap.set(nodeProps.id, node);
    this.layer.add(node);
    safeDraw(this.layer);
    return node;
  }

  public updateNode(nodeProps: NodeProperties): Konva.Node | null {
    const node = this.nodeMap.get(nodeProps.id);
    if (!node) return null;
    this.updateKonvaNode(node, nodeProps);
    safeDraw(this.layer);
    return node;
  }

  public removeNode(nodeId: string): boolean {
    const node = this.nodeMap.get(nodeId);
    if (!node) return false;
    node.destroy();
    this.nodeMap.delete(nodeId);
    safeDraw(this.layer);
    return true;
  }

  public getNode(nodeId: string): Konva.Node | undefined {
    return this.nodeMap.get(nodeId);
  }

  public getAllNodes(): Konva.Node[] {
    return Array.from(this.nodeMap.values());
  }

  public clear(): void {
    this.layer.destroyChildren();
    this.nodeMap.clear();
    safeDraw(this.layer);
  }

  private createKonvaNode(props: NodeProperties): Konva.Shape | Konva.Group {
    const commonConfig: any = {
      id: props.id,
      name: props.name || props.type,
      x: props.x,
      y: props.y,
      width: props.width,
      height: props.height,
      rotation: props.rotation || 0,
      scaleX: props.scaleX ?? 1,
      scaleY: props.scaleY ?? 1,
      opacity: props.opacity ?? 1,
      visible: props.visible ?? true,
      draggable: !props.locked,
      listening: true,
      ...(props.props || {}),
    };

    let node: Konva.Shape | Konva.Group;

    switch (props.type) {
      case 'text':
        node = new Konva.Text({
          ...commonConfig,
          text: (props.props?.text as string) || props.name || 'Text',
          fontSize: (props.props?.fontSize as number) || 16,
          fontFamily: (props.props?.fontFamily as string) || 'Inter, sans-serif',
          fill: (props.props?.fill as string) || '#FFFFFF',
        });
        break;

      case 'image':
        node = new Konva.Rect({
          ...commonConfig,
          fill: (props.props?.fill as string) || '#334155',
          stroke: (props.props?.stroke as string) || '#64748B',
          strokeWidth: (props.props?.strokeWidth as number) || 1,
        });
        break;

      case 'circle':
        node = new Konva.Circle({
          ...commonConfig,
          radius: Math.min(props.width, props.height) / 2,
          fill: (props.props?.fill as string) || '#6366F1',
        });
        break;

      case 'liquid_block':
      case 'frame':
      case 'shape':
      default:
        node = new Konva.Rect({
          ...commonConfig,
          fill: (props.props?.fill as string) || '#4F46E5',
          stroke: (props.props?.stroke as string) || '#4338CA',
          strokeWidth: (props.props?.strokeWidth as number) || 1,
          cornerRadius: (props.props?.cornerRadius as number) || 4,
        });
        break;
    }

    this.bindEvents(node, props.id);
    return node;
  }

  private updateKonvaNode(node: Konva.Node, props: NodeProperties): void {
    node.x(props.x);
    node.y(props.y);
    node.width(props.width);
    node.height(props.height);
    node.rotation(props.rotation || 0);
    node.scaleX(props.scaleX ?? 1);
    node.scaleY(props.scaleY ?? 1);
    node.opacity(props.opacity ?? 1);
    node.visible(props.visible ?? true);
    node.draggable(!props.locked);

    if (props.props) {
      node.setAttrs(props.props);
    }
  }

  private bindEvents(node: Konva.Node, nodeId: string): void {
    node.on('click tap', (e) => this.onNodeClick?.(nodeId, e));
    node.on('dragmove', (e) => this.onNodeDragMove?.(nodeId, e));
    node.on('dragend', (e) => this.onNodeDragEnd?.(nodeId, e));
    node.on('mouseenter', (e) => this.onNodeMouseEnter?.(nodeId, e));
    node.on('mouseleave', (e) => this.onNodeMouseLeave?.(nodeId, e));
  }
}
