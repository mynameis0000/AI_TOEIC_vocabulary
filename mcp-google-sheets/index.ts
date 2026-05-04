// 1. [최우선] 표준 출력(Stdout) 소음 차단 필터
// 어떤 라이브러리 로드보다 먼저 실행되어 소음을 Stderr로 격리합니다.
const originalWrite = process.stdout.write;
// @ts-ignore
process.stdout.write = (chunk, encoding, callback) => {
  const data = typeof chunk === 'string' ? chunk : chunk.toString();
  // JSON RPC 메시지({로 시작)만 Stdout으로 보내고, 나머지는 Stderr로 우회
  if (data.trim().startsWith('{')) {
    return originalWrite.call(process.stdout, chunk, encoding, callback);
  }
  return process.stderr.write(chunk, encoding, callback);
};

// 2. 라이브러리 임포트
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { google } from "googleapis";
import { JWT } from "google-auth-library";

// 3. 인증 및 컨텍스트 초기화
async function initContext() {
  const credsEnv = process.env.GOOGLE_SHEETS_CREDENTIALS;
  if (!credsEnv) {
    throw new Error("GOOGLE_SHEETS_CREDENTIALS environment variable is required");
  }

  const credentials = JSON.parse(credsEnv);
  
  // 서비스 계정 인증 방식 (MCP에 가장 적합)
  const auth = new JWT({
    email: credentials.client_email,
    key: credentials.private_key,
    scopes: ["https://www.googleapis.com/auth/spreadsheets"],
  });

  return {
    sheets: google.sheets({ version: "v4", auth }),
  };
}

// 4. MCP 서버 설정
const server = new Server(
  { name: "google-sheets-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// 도구 목록 정의
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "read_sheet",
      description: "구글 시트의 데이터를 읽어옵니다.",
      inputSchema: {
        type: "object",
        properties: {
          spreadsheetId: { type: "string" },
          range: { type: "string", description: "예: Sheet1!A1:E10" },
        },
        required: ["spreadsheetId", "range"],
      },
    },
    {
      name: "update_sheet",
      description: "구글 시트에 데이터를 씁니다.",
      inputSchema: {
        type: "object",
        properties: {
          spreadsheetId: { type: "string" },
          range: { type: "string" },
          values: { type: "array", items: { type: "array", items: { type: "string" } } },
        },
        required: ["spreadsheetId", "range", "values"],
      },
    },
  ],
}));

// 도구 실행 로직
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { sheets } = await initContext();
  const { name, arguments: args } = request.params;

  try {
    if (name === "read_sheet") {
      const response = await sheets.spreadsheets.values.get({
        spreadsheetId: args?.spreadsheetId as string,
        range: args?.range as string,
      });
      return { content: [{ type: "text", text: JSON.stringify(response.data.values) }] };
    } 
    
    if (name === "update_sheet") {
      await sheets.spreadsheets.values.update({
        spreadsheetId: args?.spreadsheetId as string,
        range: args?.range as string,
        valueInputOption: "USER_ENTERED",
        requestBody: { values: args?.values as string[][] },
      });
      return { content: [{ type: "text", text: "성공적으로 업데이트되었습니다." }] };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (error: any) {
    return {
      isError: true,
      content: [{ type: "text", text: `에러 발생: ${error.message}` }],
    };
  }
});

// 5. 서버 실행
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // Stdout 오염 방지를 위해 에러 메시지만 Stderr로 출력
  console.error("🚀 Google Sheets MCP Server running...");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});