import axios from "axios";
import TurndownService from "turndown";
import { load } from "cheerio";

async function scrapeToMarkdown(url: string): Promise<string> {
  const response = await axios.get(url);
  const html = response.data;

  const turndownService = new TurndownService();
  return turndownService.turndown(html);
}

export function extractTiogaSection(markdown: string): string {
  const lines = markdown.split("\n");
  let tiogaSection: string[] = [];
  let foundTioga = false;

  for (const line of lines) {
    if (foundTioga) {
      if (line.startsWith("Glacier Point Road")) {
        break;
      } else {
        tiogaSection.push(line);
      }
    } else if (/^Tioga Road$/.test(line)) {
      foundTioga = true;
    }
  }

  if (!foundTioga) {
    throw new Error("Could not find Tioga Road section in markdown");
  }

  return tiogaSection.join("\n");
}

export async function scrapePlowingPage(): Promise<string> {
  const URL = "https://www.nps.gov/yose/planyourvisit/tioga.htm";
  const markdown = await scrapeToMarkdown(URL);
  return markdown;
}

export async function scrapeConditionsPage(givenHtml?: string): Promise<{
  foundHtml: string;
  isOpen: boolean;
}> {
  let html;
  if (!givenHtml) {
    const URL = "https://www.nps.gov/yose/planyourvisit/conditions.htm";
    const response = await axios.get(URL);
    html = response.data;
  } else {
    html = givenHtml;
  }

  const $ = load(html);
  const tiogaElements = $("table")
    .find('strong:contains("Tioga Road")')
    .closest("tr");

  if (tiogaElements.length !== 1) {
    throw new Error("Could not find single Tioga Road section in HTML");
  }

  const tiogaElement = tiogaElements.first();
  // console.log($.html(tiogaElement));
  const isClosed =
    tiogaElement.find("*").filter((i, el) => {
      return $(el).text().trim() === "Closed";
    }).length > 0;
  const isOpen =
    tiogaElement.find("*").filter((i, el) => {
      return $(el).text().trim() === "Open";
    }).length > 0;
  if ((!isClosed && !isOpen) || (isClosed && isOpen)) {
    throw new Error("Could not determine if Tioga is open or closed");
  }
  return { foundHtml: $.html(tiogaElement), isOpen };
}
