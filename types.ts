
export enum NewsTopic {
  BRASIL = 'Brasil',
  MUNDO = 'Mundo',
  TECNOLOGIA = 'Tecnologia',
  ECONOMIA = 'Economia',
  ESPORTES = 'Esportes',
  ENTRETENIMENTO = 'Entretenimento',
  CIENCIA = 'Ciência',
  POLITICA = 'Política'
}

export interface GroundingSource {
  title: string;
  uri: string;
}

export interface NewsSummary {
  topic: NewsTopic;
  content: string;
  sources: GroundingSource[];
  timestamp: number;
}

export interface AppState {
  currentTopic: NewsTopic;
  summaries: Record<string, NewsSummary>;
  loading: boolean;
  error: string | null;
}
