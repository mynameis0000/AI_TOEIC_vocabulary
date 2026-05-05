import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { google } from "googleapis";
import { JWT } from "google-auth-library";
import * as dotenv from "dotenv";

// 환경 변수 로드
dotenv.config();

const SPREADSHEET_ID = process.env.MY_SPREADSHEET_ID;
const SERVICE_ACCOUNT_JSON = process.env.GCP_SERVICE_ACCOUNT_JSON;

if (!SPREADSHEET_ID || !SERVICE_ACCOUNT_JSON) {
  console.error("❌ 필수 환경 변수 누락되었습니다.");
  process.exit(1);
}

// 1. 서비스 계정 인증 설정
const credentials = JSON.parse(SERVICE_ACCOUNT_JSON);
const auth = new JWT({
  email: credentials.client_email,
  key: credentials.private_key,
  scopes: ["https://www.googleapis.com/auth/spreadsheets"],
});

const sheets = google.sheets({ version: "v4", auth });

// 2. MCP 서버 생성
const server = new Server(
  {
    name: "google-sheets-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// 3. 도구(Tools) 목록 정의
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "initialize_headers",
        description: "시트에 '단어, 뜻, 예문, 상태' 헤더를 생성합니다.",
        inputSchema: { type: "object", properties: {} }
      },
      {
        name: "append_word",
        description: "시트에 새로운 단어 데이터를 추가합니다.",
        inputSchema: {
          type: "object",
          properties: {
            word: { type: "string" },
            meaning: { type: "string" },
            example: { type: "string" },
          },
          required: ["word", "meaning", "example"]
        }
      }
    ]
  };
});

// 4. 도구 실행 로직
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "initialize_headers") {
      const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: "시트1!A1:D1", // 'Sheet1'에서 '시트1'로 변경
      });

      if (!response.data.values || response.data.values.length === 0) {
        await sheets.spreadsheets.values.update({
          spreadsheetId: SPREADSHEET_ID,
          range: "시트1!A1", // '시트1'로 변경
          valueInputOption: "RAW",
          requestBody: {
            values: [["단어", "뜻", "예문", "상태"]],
          },
        });
        return { content: [{ type: "text", text: "🚀 헤더 생성이 완료되었습니다." }] };
      }
      return { content: [{ type: "text", text: "✅ 헤더가 이미 존재합니다." }] };
    }

    if (name === "append_word") {
      const { word, meaning, example } = args as { word: string; meaning: string; example: string };
      await sheets.spreadsheets.values.append({
        spreadsheetId: SPREADSHEET_ID,
        range: "시트1!A:D", // '시트1'로 변경
        valueInputOption: "RAW",
        requestBody: {
          values: [[word, meaning, example, "새로움"]],
        },
      });
      return { content: [{ type: "text", text: `📝 단어 추가 완료: ${word}` }] };
    }

    throw new Error(`알 수 없는 도구: ${name}`);
  } catch (error: any) {
    return {
      isError: true,
      content: [{ type: "text", text: `오류 발생: ${error.message}` }]
    };
  }
});

// 5. 서버 실행
async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.log("🚀 Google Sheets MCP Server Running");
}

runServer().catch(console.error);