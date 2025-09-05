// Dream journal interfaces

// Image generation status enum
export const ImageGenerationStatus = {
  PENDING: 'pending',
  GENERATING: 'generating',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

export type ImageGenerationStatus =
  (typeof ImageGenerationStatus)[keyof typeof ImageGenerationStatus];

export interface Dream {
  id: number;
  description: string;
  created: string;
  updated: string;
  qualities?: Quality[];
  images?: Image[];
  is_public?: boolean;
  is_owner?: boolean;
}

export interface Quality {
  id: number;
  name: string;
  frequency: number;
}

export interface Image {
  id: number;
  generation_status: ImageGenerationStatus;
  generation_prompt: string;
  gcs_path: string;
  created: string;
  image_url?: string; // Optional signed URL when status is completed
}

export interface DreamCreate {
  description: string;
  quality_names: string[];
}

export interface Meta {
  totalCount: number;
}
