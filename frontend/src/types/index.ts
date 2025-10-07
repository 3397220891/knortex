// Entity Type Definition
export interface Entity {
  id: string;
  name: string;
  type: string;
  properties?: Record<string, any>;
  labels?: string[];
}

// Relationship Type Definition
export interface Relationship {
  id: string;
  type: string;
  source: string;
  target: string;
  properties?: Record<string, any>;
}

// Graph Data Type
export interface GraphNode {
  id: string;
  name: string;
  type: string;
  category?: string;
  symbolSize?: number;
  x?: number;
  y?: number;
  properties?: Record<string, any>;
}

export interface GraphLink {
  id: string;
  source: string;
  target: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// File Upload Type
export interface FileUpload {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  result?: any;
  error?: string;
}

// Extraction Result Type
export interface ExtractionResult {
  entities: Entity[];
  relationships: Relationship[];
  metadata: {
    file_type: string;
    content_length: number;
    processing_time: number;
  };
}

// Search Type
export interface SearchResult {
  query: string;
  results: Entity[];
  total: number;
  took: number;
}

// Application State Type
export interface AppState {
  isLoading: boolean;
  error: string | null;
  currentView: 'upload' | 'search' | 'graph' | 'entities';
  graphData: GraphData | null;
  entities: Entity[];
  searchResults: SearchResult | null;
}
