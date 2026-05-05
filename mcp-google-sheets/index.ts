import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { google } from "googleapis";
import { JWT } from "google-auth-library";

// 1. 환경 변수 및 설정
// main.py 또는 Render 대시보드에서 설정한 ID를 가져옵니다.
const SPREADSHEET_ID = process.env.MY_SPREADSHEET_ID;

if (!SPREADSHEET_ID) {
  console.error("❌ 에러: MY_SPREADSHEET_ID 환경 변수가 설정되지 않았습니다.");
  process.exit(1);
}

// 구글 서비스 계정 인증 (JSON 키 파일 경로 확인 필요)
// 보통 mcp-google-sheets 폴더 안에 있는 서비스 계정 키 파일 이름을 넣으세요.
const auth = new JWT({
  keyFile: "credentials.json", // 같은 폴더에 있으므로 파일명만 적음
  scopes: ["https://www.googleapis.com/auth/spreadsheets"],
});

const sheets = google.sheets({ version: "v4", auth });

// 2. 핵심 기능: 헤더 및 단어 처리 로직
async function processWordSheet() {
  try {
    // A1:E1 범위를 읽어 헤더가 있는지 확인합니다.
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: "Sheet1!A1:E1",
    });

    const rows = response.data.values;
    
    // 헤더가 없거나 첫 줄이 비어있다면 헤더 생성
    if (!rows || rows.length === 0) {
      console.log("📝 헤더가 없어 생성을 시작합니다...");
      await sheets.spreadsheets.values.update({
        spreadsheetId: SPREADSHEET_ID,
        range: "Sheet1!A1:E1",
        valueInputOption: "RAW",
        requestBody: {
          values: [["단어", "뜻", "예문", "퀴즈", "상태"]],
        },
      });
      console.log("✅ 헤더 생성 완료: [단어, 뜻, 예문, 퀴즈, 상태]");
    }

    // 실제 단어 데이터 읽기 (A2부터 끝까지)
    const dataResponse = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: "Sheet1!A2:E",
    });

    const dataRows = dataResponse.data.values;
    if (!dataRows || dataRows.length === 0) {
      console.log("ℹ️ 처리할 단어가 없습니다. 시트에 단어를 입력해 주세요.");
      return;
    }

    // 단어 인식 및 로직 수행 (여기서 AI 처리를 연결할 수 있습니다)
    for (let i = 0; i < dataRows.length; i++) {
      const word = dataRows[i][0];
      if (word && !dataRows[i][4]) { // 단어는 있고 '상태'가 비어있다면
        console.log(`🔍 새 단어 발견: ${word}`);
        // TODO: 여기서 Gemini API를 호출하여 뜻/예문/퀴즈를 생성하는 로직 추가 가능
      }
    }

  } catch (error) {
    console.error("❌ 시트 처리 중 상세 오류:", error);
  }
}

// 3. MCP 서버 설정
const server = new Server(
  {
    name: "google-sheets-word-master",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// 도구 목록 정의 (필요 시)
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "sync_words",
      description: "구글 시트의 단어를 읽고 AI 퀴즈를 업데이트합니다.",
    },
  ],
}));

// 도구 실행 로직
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "sync_words") {
    await processWordSheet();
    return {
      content: [{ type: "text", text: "동기화가 완료되었습니다." }],
    };
  }
  throw new Error("Unknown tool");
});

// 서버 실행 및 초기 실행
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.log("🚀 Google Sheets MCP Server Running");
  
  // 서버 시작 시 즉시 한 번 실행
  await processWordSheet();
}

main().catch(console.error);