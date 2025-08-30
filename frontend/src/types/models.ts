// Dream journal interfaces
export interface Dream {
  id: number;
  description: string;
  created: string;
  updated: string;
  qualities?: Quality[];
}

export interface Quality {
  id: number;
  name: string;
  frequency: number;
}

export interface DreamCreate {
  description: string;
  quality_names: string[];
}

export interface Meta {
  totalCount: number;
}
