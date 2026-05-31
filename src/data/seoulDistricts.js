// Seoul district metadata.
// The precise map geometry now lives in `seoul_municipalities_geo_simple.json`.
// Keep these stable ids because they are used by UI state and future real-estate APIs.
export const seoulDistricts = [
  { id: "eunpyeong-gu", name: "은평구", nameEng: "Eunpyeong-gu", lawdCode: "11380" },
  { id: "dobong-gu", name: "도봉구", nameEng: "Dobong-gu", lawdCode: "11320" },
  { id: "gangbuk-gu", name: "강북구", nameEng: "Gangbuk-gu", lawdCode: "11305" },
  { id: "nowon-gu", name: "노원구", nameEng: "Nowon-gu", lawdCode: "11350" },
  { id: "seodaemun-gu", name: "서대문구", nameEng: "Seodaemun-gu", lawdCode: "11410" },
  { id: "jongno-gu", name: "종로구", nameEng: "Jongno-gu", lawdCode: "11110" },
  { id: "seongbuk-gu", name: "성북구", nameEng: "Seongbuk-gu", lawdCode: "11290" },
  { id: "jungnang-gu", name: "중랑구", nameEng: "Jungnang-gu", lawdCode: "11260" },
  { id: "mapo-gu", name: "마포구", nameEng: "Mapo-gu", lawdCode: "11440" },
  { id: "jung-gu", name: "중구", nameEng: "Jung-gu", lawdCode: "11140" },
  { id: "dongdaemun-gu", name: "동대문구", nameEng: "Dongdaemun-gu", lawdCode: "11230" },
  { id: "gwangjin-gu", name: "광진구", nameEng: "Gwangjin-gu", lawdCode: "11215" },
  { id: "yongsan-gu", name: "용산구", nameEng: "Yongsan-gu", lawdCode: "11170" },
  { id: "seongdong-gu", name: "성동구", nameEng: "Seongdong-gu", lawdCode: "11200" },
  { id: "gangseo-gu", name: "강서구", nameEng: "Gangseo-gu", lawdCode: "11500" },
  { id: "yangcheon-gu", name: "양천구", nameEng: "Yangcheon-gu", lawdCode: "11470" },
  { id: "guro-gu", name: "구로구", nameEng: "Guro-gu", lawdCode: "11530" },
  { id: "yeongdeungpo-gu", name: "영등포구", nameEng: "Yeongdeungpo-gu", lawdCode: "11560" },
  { id: "dongjak-gu", name: "동작구", nameEng: "Dongjak-gu", lawdCode: "11590" },
  { id: "geumcheon-gu", name: "금천구", nameEng: "Geumcheon-gu", lawdCode: "11545" },
  { id: "gwanak-gu", name: "관악구", nameEng: "Gwanak-gu", lawdCode: "11620" },
  { id: "seocho-gu", name: "서초구", nameEng: "Seocho-gu", lawdCode: "11650" },
  { id: "gangnam-gu", name: "강남구", nameEng: "Gangnam-gu", lawdCode: "11680" },
  { id: "songpa-gu", name: "송파구", nameEng: "Songpa-gu", lawdCode: "11710" },
  { id: "gangdong-gu", name: "강동구", nameEng: "Gangdong-gu", lawdCode: "11740" }
];

export const districtNameToId = Object.fromEntries(
  seoulDistricts.map((district) => [district.name, district.id])
);

export const districtIdToMeta = Object.fromEntries(
  seoulDistricts.map((district) => [district.id, district])
);

export const districtDetails = {
  "gangnam-gu": {
    trend: "최근 3개월 실거래가 추이 카드 영역",
    complexes: ["래미안대치팰리스", "은마아파트", "압구정현대"]
  },
  "seocho-gu": {
    trend: "서초권역 주요 가격 흐름 카드 영역",
    complexes: ["반포자이", "아크로리버파크", "래미안원베일리"]
  },
  "songpa-gu": {
    trend: "잠실/송파 실거래 추이 카드 영역",
    complexes: ["잠실엘스", "리센츠", "헬리오시티"]
  }
};
