// // api.js

// /**
//  * 1. 단어 생성 요청 (AI로부터 의미와 품사 정보 가져오기)
//  * @param {string} word - 검색할 단어
//  * @returns {Promise<Object>} 서버로부터 받은 단어 정보
//  */
// export async function fetchWord(word) {
//     try {
//         const response = await fetch("/generate", {
//             method: "POST",
//             headers: {
//                 "Content-Type": "application/json"
//             },
//             body: JSON.stringify({ word })
//         });

//         if (!response.ok) {
//             throw new Error(`Server error: ${response.status}`);
//         }

//         return await response.json();
//     } catch (error) {
//         console.error("API fetchWord error:", error);
//         throw error; // 호출한 곳(main.js)에서 에러를 핸들링하도록 던짐
//     }
// }

// /**
//  * 2. 데이터 내보내기 요청 (PDF 또는 XLSX 파일 다운로드)
//  * @param {string} type - 'pdf' 또는 'xlsx'
//  * @param {Array} rows - 내보낼 단어 데이터 배열
//  * @returns {Promise<Blob>} 파일 데이터(Blob)
//  */
// export async function exportData(type, rows) {
//     try {
//         const response = await fetch(`/export/${type}`, {
//             method: "POST",
//             headers: {
//                 "Content-Type": "application/json"
//             },
//             body: JSON.stringify({ words: rows })
//         });

//         if (!response.ok) {
//             throw new Error(`Export error: ${response.status}`);
//         }

//         return await response.blob();
//     } catch (error) {
//         console.error("API exportData error:", error);
//         throw error;
//     }
// }

// api.js

/**
 * 1. 단어 생성 요청 (AI로부터 의미와 품사 정보 가져오기)
 */
export async function fetchWord(word) {
  try {
    const response = await fetch("/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ word }),
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API fetchWord error:", error);
    throw error;
  }
}

/**
 * 2. 데이터 내보내기 요청 (PDF 또는 XLSX 파일 다운로드)
 */
export async function exportData(type, rows) {
  try {
    const response = await fetch(`/export/${type}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ words: rows }),
    });

    if (!response.ok) {
      throw new Error(`Export error: ${response.status}`);
    }

    return await response.blob();
  } catch (error) {
    console.error("API exportData error:", error);
    throw error;
  }
}