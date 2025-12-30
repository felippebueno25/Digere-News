
import { GoogleGenAI, GenerateContentResponse, Modality } from "@google/genai";
import { NewsTopic, NewsSummary, GroundingSource } from "../types";

export function decodeBase64(base64: string) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

export async function decodeAudioData(
  data: Uint8Array,
  ctx: AudioContext,
  sampleRate: number,
  numChannels: number,
): Promise<AudioBuffer> {
  const dataInt16 = new Int16Array(data.buffer);
  const frameCount = dataInt16.length / numChannels;
  const buffer = ctx.createBuffer(numChannels, frameCount, sampleRate);

  for (let channel = 0; channel < numChannels; channel++) {
    const channelData = buffer.getChannelData(channel);
    for (let i = 0; i < frameCount; i++) {
      channelData[i] = dataInt16[i * numChannels + channel] / 32768.0;
    }
  }
  return buffer;
}

export const fetchNewsSummary = async (topic: NewsTopic): Promise<NewsSummary> => {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  
  const prompt = `Você é um Analista de Inteligência Sênior com foco em curadoria de notícias de alto impacto sobre "${topic}".

Sua missão é realizar uma "digestão completa" das fontes mais recentes.

ETAPAS DE PROCESSAMENTO:
1. PESQUISA: Localize os 5 artigos mais influentes das últimas 24h.
2. EXTRAÇÃO: Capture dados concretos, percentuais, nomes de autoridades e horários. Ignore "clickbait".
3. SÍNTESE: Crie um resumo ultra-denso focado em VALOR e TEMPO para o leitor.

ESTRUTURA OBRIGATÓRIA (MARKDOWN):
# [Título Criativo e Informativo]
## Por que isso importa hoje?
[Resumo de 2 parágrafos com as principais manchetes cruzadas]

## Prato Principal (Os Fatos)
- **[Destaque 1]:** [Explicação densa com dados]
- **[Destaque 2]:** [Explicação densa com dados]
- **[Destaque 3]:** [Explicação densa com dados]

## Sobremesa (Análise de Contexto)
[Explique a tendência ou o que esperar nas próximas horas/dias]

REGRAS:
- Nunca use frases vazias como "Várias coisas aconteceram". Seja específico.
- Idioma: Português Brasileiro nativo.
- Use negrito em nomes próprios e dados numéricos.`;

  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: prompt,
      config: {
        tools: [{ googleSearch: {} }],
        temperature: 0.2, // Máxima precisão e foco nos fatos
      },
    });

    const text = response.text || "Ocorreu um erro na digestão dos dados.";
    const sources: GroundingSource[] = [];
    const chunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;
    
    if (chunks) {
      chunks.forEach((chunk: any) => {
        if (chunk.web && chunk.web.uri && chunk.web.title) {
          if (!sources.find(s => s.uri === chunk.web.uri)) {
            sources.push({ title: chunk.web.title, uri: chunk.web.uri });
          }
        }
      });
    }

    return {
      topic,
      content: text,
      sources: sources.slice(0, 8),
      timestamp: Date.now()
    };
  } catch (error) {
    console.error("Gemini API Error:", error);
    throw new Error("Não foi possível processar as notícias. Tente novamente em instantes.");
  }
};

export const generateSpeech = async (text: string): Promise<Uint8Array> => {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  
  const cleanText = text
    .replace(/[#*`]/g, '')
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
    .slice(0, 1500);

  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash-preview-tts",
    contents: [{ parts: [{ text: `Narração profissional de resumo de notícias: ${cleanText}` }] }],
    config: {
      responseModalities: [Modality.AUDIO],
      speechConfig: {
        voiceConfig: {
          prebuiltVoiceConfig: { voiceName: 'Zephyr' }, 
        },
      },
    },
  });

  const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
  if (!base64Audio) throw new Error("Áudio indisponível.");
  
  return decodeBase64(base64Audio);
};
