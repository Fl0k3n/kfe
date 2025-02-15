export type SemanticSearchVariant =
  | "similar-description"
  | "similar-metadata"
  | "similar-llm-description"
  | "similar-images"
  | "similar-videos"
  | "similar-to-pasted";

export type FileId = number;
export type EncodedImage = string;

export type SemanticSearchRequest = {
  data: FileId | EncodedImage;
  variant: SemanticSearchVariant;
};

export type QueryBasedSearchRequest = {
  query: string;
};

export type HistoryItem = {
  isQuery: boolean;
  item: SemanticSearchRequest | QueryBasedSearchRequest;
};

export class HistoryStack {
  private stack: HistoryItem[];

  constructor() {
    this.stack = [];
  }

  pushQuery(item: QueryBasedSearchRequest) {
    this.stack.push({ isQuery: true, item });
  }

  pushSemantic(item: SemanticSearchRequest) {
    this.stack.push({ isQuery: false, item });
  }

  pop(): HistoryItem | undefined {
    return this.stack.pop();
  }

  peek(): HistoryItem | undefined {
    if (this.isEmpty()) {
      return undefined;
    }
    return this.stack[this.stack.length - 1];
  }

  isEmpty(): boolean {
    return this.stack.length === 0;
  }

  print() {
    console.log(
      this.stack.map((x) => {
        if (x.isQuery) {
          return (x.item as QueryBasedSearchRequest).query;
        } else {
          return (x.item as SemanticSearchRequest).variant;
        }
      })
    );
  }
}
