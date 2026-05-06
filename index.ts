import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { google } from "googleapis";

// --- [신경 써야 할 부분 1: 환경 변수 호출] ---
// Render의 Environment Variables에 설정한 MY_SPREADSHEET_ID를 가져옵니다.
const SPREADSHEET_ID = process.env.MY_SPREADSHEET_ID; 
const RANGE = "시트1!A:C"; 

// 구글 인증 설정
const auth = new google.auth.GoogleAuth({
  scopes: ["https://www.googleapis.com/auth/spreadsheets"],
});

const sheets = google.sheets({ version: "v4", auth });

const server = new Server(
  { name: "word-master-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// 도구 목록 정의
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "update_row",
      description: "구글 시트에 단어, 뜻, 예문을 업데이트합니다.",
      inputSchema: {
        type: "object",
        properties: {
          word: { type: "string" },
          meaning: { type: "string" },
          example: { type: "string" },
        },
        required: ["word", "meaning", "example"],
      },
    },
  ],
}));

// 도구 실행 로직
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "update_row") {
    const { word, meaning, example } = request.params.arguments as any;

    if (!SPREADSHEET_ID) {
      return {
        isError: true,
        content: [{ type: "text", text: "Error: MY_SPREADSHEET_ID 환경 변수가 설정되지 않았습니다." }],
      };
    }

    try {
      // 1. 기존 데이터 가져오기
      const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: RANGE,
      });

      const rows = response.data.values || [];
      const rowIndex = rows.findIndex((row) => row[0] === word);

      if (rowIndex !== -1) {
        // 2. 해당 행 업데이트 (B열과 C열)
        await sheets.spreadsheets.values.update({
          spreadsheetId: SPREADSHEET_ID,
          range: `시트1!B${rowIndex + 1}:C${rowIndex + 1}`,
          valueInputOption: "RAW",
          requestBody: { values: [[meaning, example]] },
        });
        return { content: [{ type: "text", text: `✅ ${word} 업데이트 완료` }] };
      }
      return { content: [{ type: "text", text: "❌ 시트에서 해당 단어를 찾을 수 없습니다." }] };
    } catch (error: any) {
      return {
        isError: true,
        content: [{ type: "text", text: `Error: ${error.message}` }],
      };
    }
  }
  throw new Error("Tool not found");
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("🚀 MCP 시트 서버가 실행 중입니다.");