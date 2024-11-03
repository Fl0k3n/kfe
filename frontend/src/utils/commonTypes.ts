import { FileMetadataDTO } from "../api";

export type DataSource = "all" | "search" | "embedding-similarity";

export type FileWithScoresMaybe = FileMetadataDTO & {
  denseScore?: number;
  totalScore?: number;
  lexicalScore?: number;
};

export type FileListItem = {
  file: FileMetadataDTO;
  caption?: string;
};

export type Scroller = {
  scrollToTop: () => void;
  scrollToIdx: (idx: number) => void;
};

export type NavigationContext = {
  navigatedFromViewIdx: number;
  searchQuery: string;
  dataSource: DataSource;
  embeddingSimilarityItems: FileWithScoresMaybe[];
};
