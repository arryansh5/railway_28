function distance(coord1: number[], coord2: number[]) {
  const R = 6371; // km
  const dLat = (coord2[1] - coord1[1]) * Math.PI / 180;
  const dLon = (coord2[0] - coord1[0]) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(coord1[1] * Math.PI / 180) * Math.cos(coord2[1] * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

function getTrackDistance(coords: number[][]) {
  let d = 0;
  for(let i=0; i<coords.length-1; i++) d += distance(coords[i], coords[i+1]);
  return d;
}

export function buildGraph(stationsMeta: any) {
  const adj: Record<string, any[]> = {};
  for (const [id, meta] of Object.entries(stationsMeta)) {
    if (!adj[id]) adj[id] = [];
    for (const branch of (meta as any).connectedBranches || []) {
      const dist = getTrackDistance(branch.trackCoords);
      
      // Ensure we don't add duplicate edges
      if (!adj[id].find(e => e.to === branch.mainStationId)) {
        adj[id].push({ to: branch.mainStationId, dist, coords: branch.trackCoords });
      }
      
      if (!adj[branch.mainStationId]) adj[branch.mainStationId] = [];
      if (!adj[branch.mainStationId].find(e => e.to === id)) {
        adj[branch.mainStationId].push({ 
          to: id, 
          dist, 
          coords: [...branch.trackCoords].reverse() 
        });
      }
    }
  }
  return adj;
}

class MinHeap {
  private heap: { id: string; d: number }[] = [];

  push(val: { id: string; d: number }) {
    this.heap.push(val);
    this.bubbleUp(this.heap.length - 1);
  }

  pop() {
    if (this.heap.length === 1) return this.heap.pop();
    const top = this.heap[0];
    this.heap[0] = this.heap.pop()!;
    this.sinkDown(0);
    return top;
  }

  isEmpty() {
    return this.heap.length === 0;
  }

  private bubbleUp(idx: number) {
    const el = this.heap[idx];
    while (idx > 0) {
      const parentIdx = Math.floor((idx - 1) / 2);
      const parent = this.heap[parentIdx];
      if (el.d >= parent.d) break;
      this.heap[parentIdx] = el;
      this.heap[idx] = parent;
      idx = parentIdx;
    }
  }

  private sinkDown(idx: number) {
    const length = this.heap.length;
    const el = this.heap[idx];
    while (true) {
      let leftIdx = 2 * idx + 1;
      let rightIdx = 2 * idx + 2;
      let swapIdx = null;

      if (leftIdx < length) {
        if (this.heap[leftIdx].d < el.d) swapIdx = leftIdx;
      }
      if (rightIdx < length) {
        if (
          (swapIdx === null && this.heap[rightIdx].d < el.d) ||
          (swapIdx !== null && this.heap[rightIdx].d < this.heap[leftIdx].d)
        ) {
          swapIdx = rightIdx;
        }
      }
      if (swapIdx === null) break;
      this.heap[idx] = this.heap[swapIdx];
      this.heap[swapIdx] = el;
      idx = swapIdx;
    }
  }
}

export function findPaths(adj: Record<string, any[]>, fromId: string, toId: string, maxPaths: number, stationsMeta: any) {
  // 1. Reverse Dijkstra: find shortest distance from all nodes to `toId`
  const distToTarget: Record<string, number> = {};
  const pq = new MinHeap();
  pq.push({ id: toId, d: 0 });
  distToTarget[toId] = 0;
  
  while (!pq.isEmpty()) {
    const curr = pq.pop()!;
    if (curr.d > (distToTarget[curr.id] ?? Infinity)) continue;
    
    // We traverse reverse edges. Since graph is undirected, adj[curr.id] has all neighbors.
    for (const edge of adj[curr.id] || []) {
      const nd = curr.d + edge.dist;
      if (nd < (distToTarget[edge.to] ?? Infinity)) {
        distToTarget[edge.to] = nd;
        pq.push({ id: edge.to, d: nd });
      }
    }
  }
  
  const shortestDist = distToTarget[fromId];
  if (shortestDist === undefined) return []; // No path
  
  const paths: any[] = [];
  const maxDist = shortestDist * 1.2; // Explore up to 20% longer
  let iterations = 0;
  let abort = false;
  
  function dfs(currId: string, currentPath: any[], currentDist: number, visited: Set<string>) {
    if (abort || paths.length >= maxPaths) return;
    if (iterations > 50000) {
      abort = true;
      return;
    }
    iterations++;
    
    // A* Pruning: if current distance + best possible remaining distance > maxDist, prune!
    if (currentDist + (distToTarget[currId] ?? Infinity) > maxDist) return;
    
    if (currId === toId) {
      paths.push({ dist: currentDist, segments: [...currentPath] });
      return;
    }
    
    // Sort edges by `edge.dist + distToTarget[edge.to]` to greedily explore the best paths first
    const edges = (adj[currId] || []).sort((a,b) => {
      const scoreA = a.dist + (distToTarget[a.to] ?? Infinity);
      const scoreB = b.dist + (distToTarget[b.to] ?? Infinity);
      return scoreA - scoreB;
    });

    for (const edge of edges) {
      if (abort || paths.length >= maxPaths) break;
      // STRICT RULE: We cannot route THROUGH a middle station!
      // A middle station can only be the start or the end of a journey.
      if (edge.to !== toId && stationsMeta[edge.to]?.stationClass !== 'main') {
        continue;
      }

      if (!visited.has(edge.to)) {
        visited.add(edge.to);
        currentPath.push(edge);
        dfs(edge.to, currentPath, currentDist + edge.dist, visited);
        currentPath.pop();
        visited.delete(edge.to);
      }
    }
  }
  
  dfs(fromId, [], 0, new Set([fromId]));
  
  // Sort paths by distance first
  paths.sort((a, b) => a.dist - b.dist);

  // Filter out paths that are too similar (Jaccard similarity > 0.75)
  // This removes fake alternatives that just take a tiny detour around a city.
  const distinctPaths: any[] = [];
  for (const path of paths) {
    const pathNodes = new Set(path.segments.map((s: any) => s.to));
    let isDistinct = true;
    for (const dPath of distinctPaths) {
      const dPathNodes = new Set(dPath.segments.map((s: any) => s.to));
      let intersection = 0;
      for (const node of pathNodes) {
        if (dPathNodes.has(node)) intersection++;
      }
      const union = pathNodes.size + dPathNodes.size - intersection;
      const similarity = intersection / union;
      
      // If paths share more than 75% of their stations, consider them the same
      if (similarity > 0.75) {
        isDistinct = false;
        break;
      }
    }
    if (isDistinct) {
      distinctPaths.push(path);
    }
  }
  
  return distinctPaths;
}
