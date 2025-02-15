import { useCallback, useEffect, useRef, useState } from "react";
import { getApis } from "../api/initializeApis";

export const useAllFilesProvider = (directory: string, fetchLimit: number) =>
  useCallback(
    (offset: number) => {
      return getApis()
        .filesApi.getDirectoryFilesFilesGet({
          offset,
          limit: fetchLimit,
          xDirectory: directory,
        })
        .then((x) => ({
          data: x.files,
          offset: x.offset,
          total: x.total,
        }));
    },
    [directory, fetchLimit]
  );

export const useSearchedFilesProvider = (
  directory: string,
  searchQuery: string,
  fetchLimit: number
) =>
  useCallback(
    (offset: number) => {
      return getApis()
        .filesApi.searchFilesSearchPost({
          offset,
          limit: fetchLimit,
          searchRequest: { query: searchQuery },
          xDirectory: directory,
        })
        .then((x) => ({
          data: x.results.map((item) => ({
            ...item.file,
            denseScore: item.denseScore,
            lexicalScore: item.lexicalScore,
            totalScore: item.totalScore,
          })),
          offset: x.offset,
          total: x.total,
        }));
    },
    [searchQuery, directory, fetchLimit]
  );

export type PaginatedDataResponse<T> = {
  data: T[];
  offset: number;
  total: number;
};

type FetchingState<T> = {
  isLoading: boolean[];
  ready: boolean[];
  buff: (T | undefined)[];
};

const boolArrayToString = (arr: boolean[]) =>
  arr.map((x) => (x ? "1" : "0")).join("");

export function usePaginatedQuery<T>(
  queryLimit: number,
  dataProvider?: (offset: number) => Promise<PaginatedDataResponse<T>>
) {
  // used to rerender component when buff status changes
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_, setBuffStatus] = useState<string>("");
  const [loaded, setLoaded] = useState(false);
  const fetchingStateRef = useRef<FetchingState<T>>({
    isLoading: [],
    ready: [],
    buff: [],
  });

  const itemGetter = useCallback(
    (idx: number): T | undefined => {
      if (idx < 0) return undefined;
      if (idx >= fetchingStateRef.current.buff.length) {
        return undefined;
      }
      if (fetchingStateRef.current.buff[idx] != null) {
        return fetchingStateRef.current.buff[idx];
      }
      const batchIdx = Math.floor(idx / queryLimit);
      if (!fetchingStateRef.current.isLoading[batchIdx] && dataProvider) {
        fetchingStateRef.current.isLoading[batchIdx] = true;
        dataProvider(batchIdx * queryLimit)
          .then((res) => {
            res.data.forEach((item, idx) => {
              fetchingStateRef.current.buff[res.offset + idx] = item;
            });
            fetchingStateRef.current.ready[batchIdx] = true;
          })
          .finally(() => {
            fetchingStateRef.current.isLoading[batchIdx] = false;
            setBuffStatus(boolArrayToString(fetchingStateRef.current.ready));
          });
      }
      return undefined;
    },
    [dataProvider, queryLimit]
  );

  useEffect(() => {
    if (!dataProvider) {
      return;
    }
    const loadFirstBatch = async () => {
      const resp = await dataProvider(0);
      const buff = Array(resp.total).fill(undefined);
      resp.data.forEach((item, idx) => {
        buff[idx] = item;
      });

      const numBatches = Math.ceil(resp.total / queryLimit);
      fetchingStateRef.current = {
        isLoading: Array(numBatches).fill(false),
        ready: Array(numBatches).fill(false),
        buff: buff,
      };
      fetchingStateRef.current.ready[0] = true;
      setBuffStatus(boolArrayToString(fetchingStateRef.current.ready));
      setLoaded(true);
    };
    setBuffStatus("");
    setLoaded(false);
    fetchingStateRef.current = {
      isLoading: [],
      ready: [],
      buff: [],
    };
    loadFirstBatch();
  }, [queryLimit, dataProvider]);

  return {
    loaded,
    numTotalItems: fetchingStateRef.current.buff.length,
    getItem: itemGetter,
  };
}

export function usePaginatedQueryExtraData<T>(
  totalItems: number | undefined,
  defaultValue: T
) {
  const dataRef = useRef<T[] | null>(null);
  useEffect(() => {
    if (totalItems) {
      dataRef.current = Array(totalItems).fill(defaultValue);
    }
  }, [totalItems, defaultValue]);

  const updateExtraData = useCallback(
    (index: number, newValue: T) => {
      if (index >= (totalItems ?? 0) || !dataRef.current) return;
      dataRef.current[index] = newValue;
    },
    [totalItems]
  );

  const getExtraData = useCallback(
    (index: number) => {
      if (index >= (totalItems ?? 0) || !dataRef.current) return undefined;
      return dataRef.current[index];
    },
    [totalItems]
  );

  return {
    updateExtraData,
    getExtraData,
  };
}
