import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { google } from "googleapis";
import { JWT } from "google-auth-library";
import * as dotenv from "dotenv";

dotenv.config();

const SPREADSHEET_ID = process.env.MY_SPREADSHEET_ID;
const SERVICE_ACCOUNT_JSON = process.env.GCP_SERVICE_ACCOUNT_JSON;

if (!SPREADSHEET_ID || !SERVICE_ACCOUNT_JSON) {
  console.error("❌ 필수 환경 변수 누락");
  process.exit(1);
}

const credentials = JSON.parse(SERVICE_ACCOUNT_JSON);
const auth = new JWT({
  email: credentials.client_email,
  key: credentials.private_key,
  scopes: ["https://www.googleapis.com/auth/spreadsheets"],
});

const sheets = google.sheets({ version: "v4", auth });

const server = new Server(
  { name: "google-sheets-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// 1. 도구 정의 (update_row 추가)
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "initialize_headers",
        description: "시트에 헤더를 생성합니다.",
        inputSchema: { type: "object", properties: {} }
      },
      {
        name: "update_row",
        description: "특정 단어가 있는 행을 찾아 뜻과 예문을 업데이트합니다.",
        inputSchema: {
          type: "object",
          properties: {
            word: { type: "string", description: "찾을 단어" },
            meaning: { type: "string", description: "채워넣을 뜻" },
            example: { type: "string", description: "채워넣을 예문" },
          },
          required: ["word", "meaning", "example"]
        }
      }
    ]
  };
});

// 2. 실행 로직
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "initialize_headers") {
      await sheets.spreadsheets.values.update({
        spreadsheetId: SPREADSHEET_ID,
        range: "시트1!A1",
        valueInputOption: "RAW",
        requestBody: { values: [["단어", "뜻", "예문", "상태"]] },
      });
      return { content: [{ type: "text", text: "🚀 헤더 생성 완료" }] };
    }

    if (name === "update_row") {
      const { word, meaning, example } = args as { word: string; meaning: string; example: string };
      
      // A열(단어) 전체를 가져와서 해당 단어가 몇 번째 줄에 있는지 찾습니다.
      const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: "시트1!A:A",
      });

      const rows = response.data.values || [];
      const rowIndex = rows.findIndex(r => r[0] === word);

      if (rowIndex === -1) {
        return { isError: true, content: [{ type: "text", text: `❌ 단어 '${word}'를 찾을 수 없습니다.` }] };
      }

      // 해당 행의 B, C, D열(뜻, 예문, 상태)을 업데이트합니다.
      const range = `시트1!B${rowIndex + 1}:D${rowIndex + 1}`;
      await sheets.spreadsheets.values.update({
        spreadsheetId: SPREADSHEET_ID,
        range,
        valueInputOption: "RAW",
        requestBody: {
          values: [[meaning, example, "AI완료"]],
        },
      });

      return { content: [{ type: "text", text: `✅ '${word}' 업데이트 완료 (행: ${rowIndex + 1})` }] };
    }

    throw new Error(`알 수 없는 도구: ${name}`);
  } catch (error: any) {
    return { isError: true, content: [{ type: "text", text: `오류: ${error.message}` }] };
  }
});

async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

runServer().catch(console.error);