import { NextRequest } from "next/server";
import { OpenAI } from "openai";



const client = new OpenAI(
  {
    apiKey: process.env.OPEN_API_KEY,
    baseURL: "https://build.lewisnote.com/v1"
  }
)


export async function POST(req: NextRequest) {
  const body = await req.json();
  const { stats, prediction, history } = body;

  const systemPrompt = `Tu es un expert en qualité de l'air et santé publique spécialisé sur Cotonou, Bénin.
        Tu analyses des données de pollution atmosphérique en temps réel et fournis des recommandations concrètes, actionnables et contextualisées à la réalité locale de Cotonou.
        Tes recommandations doivent :
      - Être basées UNIQUEMENT sur les données fournies (ne pas inventer des valeurs)
      - Mentionner des lieux et contextes précis de Cotonou (Dantokpa, Étoile Rouge, Route des Pêches, Zémidjan, etc.) quand pertinent
      - Distinguer les populations vulnérables (enfants, personnes âgées, asthmatiques, vendeurs de rue)
      - Proposer des actions concrètes adaptées au contexte béninois
      - Comparer avec les seuils OMS et expliquer l'impact sanitaire
      - Utiliser un ton professionnel mais accessible

      Réponds UNIQUEMENT en JSON valide avec cette structure exacte (pas de markdown, pas de backticks) :
      {
        "niveau_global": "Bon|Modéré|Mauvais|Très Mauvais",
        "score_risque": 0-100,
        "resume": "2-3 phrases résumant la situation actuelle",
        "insights": [
          {
            "categorie": "Feature ML|Santé|Tendance|Anomalie|Saisonnalité",
            "priorite": "haute|moyenne|basse",
            "titre": "titre court",
            "texte": "explication détaillée avec données",
            "action": "recommandation concrète"
          }
        ],
        "recommandations_population": {
          "grand_public": ["conseil 1", "conseil 2", "conseil 3"],
          "vulnerables": ["conseil 1", "conseil 2", "conseil 3"],
          "activites_ext": ["conseil 1", "conseil 2", "conseil 3" ]
        },
        "prevision_commentaire": "commentaire sur la prévision J+1",
        "alerte": null
      }

      Si le niveau est Mauvais ou Très Mauvais, "alerte" doit être une chaîne non nulle décrivant l'urgence.`;

      const userPrompt = `Voici les données actuelles de qualité de l'air à Cotonou :

        ## Statistiques globales (période complète)
        - PM2.5 moyen : ${stats.pm25Mean} μg/m³ (seuil OMS : 12 μg/m³)
        - PM10 moyen : ${stats.pm10Mean} μg/m³ (seuil OMS : 35 μg/m³)  
        - Ozone moyen : ${stats.o3Mean} μg/m³ (seuil OMS : 100 μg/m³)
        - NO₂ moyen : ${stats.no2Mean} μg/m³ (seuil OMS : 10 μg/m³)
        - AQI moyen : ${stats.aqiMean}
        - PM2.5 P95 : ${stats.pm25P95} μg/m³
        - Ratio PM2.5/PM10 : ${stats.pmRatio} (indicateur source pollution)
        - Heures en zone Mauvais (AQI > 35.5) : ${stats.mauvaisPct}%
        - Heures en zone Très mauvais (AQI > 60) : ${stats.tresMauvaisPct}%
        - Total mesures : ${stats.totalRecords}

        ## Corrélations clés
        - Corrélation PM2.5/PM10 : ${stats.corrPm}
        - Corrélation AQI/PM2.5 : ${stats.corrAqiPm25}

        ## Prévision IA J+1
        ${prediction ? `
        - PM2.5 actuel : ${prediction.current_pm25} μg/m³
        - PM2.5 prévu : ${prediction.predicted_pm25} μg/m³
        - Variation : ${prediction.delta > 0 ? "+" : ""}${prediction.delta} μg/m³
        - Label AQI prévu : ${prediction.aqi_label}
        - Conseil système : ${prediction.conseil}
        - Date prévision : ${prediction.date_prevision}
        ` : "Prévision non disponible"}

        ## Historique récent (7 derniers jours) — PM2.5 journalier
        ${history ? history.dates.map((d: string, i: number) => `- ${d} : ${history.values[i]} μg/m³`).join("\n") : "Historique non disponible"}

        ## Contexte saisonnier
        Cotonou est en période ${stats.moisActuel}. ${stats.isHarmattan ? "C'est la saison de l'Harmattan (vents sahéliens chargés de poussières)." : "Saison pluvieuse — la pluie réduit généralement les particules fines."}

        Génère une analyse complète et des recommandations basées sur ces données.`;

  const stream = await client.chat.completions.create({
    messages:[
      {
        "role": "system", content: systemPrompt
      },
      {
        "role": "user", content: userPrompt
      }
    ],
    model: "gpt-5.4",
    stream: true,
    response_format: {"type":"json_object"},
    temperature: 0.2,
  });

  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of stream) {
          controller.enqueue(encoder.encode(chunk.choices[0].delta?.content || ""));
        }
      } catch (error) {
        controller.error(error);
      } finally {
        controller.close();
      }
    },
  });
  
  return new Response(readable, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Transfer-Encoding": "chunked",
      "Cache-Control": "no-cache",
    },
  });
}