import { useMutation } from "@tanstack/react-query";
import { useContext } from "react";
import { FileMetadataDTO, SearchResultDTO } from "../api";
import { getApis } from "../api/initializeApis";
import { SelectedDirectoryContext } from "./directoryctx";
import { SemanticSearchRequest } from "./history";

export const useOpenFileMutation = () => {
  const directory = useContext(SelectedDirectoryContext) ?? "";
  const openFileMutation = useMutation({
    mutationFn: (file: FileMetadataDTO) =>
      getApis().accessApi.openFileAccessOpenPost({
        openFileRequest: { fileId: file.id },
        xDirectory: directory,
      }),
  });
  return openFileMutation.mutate;
};

export const useSemanticSearchMutations = (
  directory: string,
  onSuccess: (request: SemanticSearchRequest, data: SearchResultDTO[]) => void
) => {
  const findItemsWithSimilarDescriptionMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().filesApi.findItemsWithSimilarDescriptionsFilesFindWithSimilarDescriptionPost(
        {
          findSimilarItemsRequest: { fileId },
          xDirectory: directory,
        }
      ),
    onSuccess: (data, input) =>
      onSuccess({ data: input, variant: "similar-description" }, data),
  });

  const findItemsWithSimilarLLMDescriptionMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().filesApi.findItemsWithSimilarLlmTextFilesFindWithSimilarLlmTextPost(
        {
          findSimilarItemsRequest: { fileId },
          xDirectory: directory,
        }
      ),
    onSuccess: (data, input) =>
      onSuccess({ data: input, variant: "similar-llm-description" }, data),
  });

  const findSemanticallySimilarItemsMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().filesApi.findItemsWithSimilarMetadataFilesFindWithSimilarMetadataPost(
        {
          findSimilarItemsRequest: { fileId },
          xDirectory: directory,
        }
      ),
    onSuccess: (data, input) =>
      onSuccess({ data: input, variant: "similar-metadata" }, data),
  });

  const findVisuallySimilarImagesMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().filesApi.findVisuallySimilarImagesFilesFindVisuallySimilarImagesPost(
        {
          findSimilarItemsRequest: { fileId },
          xDirectory: directory,
        }
      ),
    onSuccess: (data, input) =>
      onSuccess({ data: input, variant: "similar-images" }, data),
  });

  const findVisuallySimilarVideosMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().filesApi.findVisuallySimilarVideosFilesFindVisuallySimilarVideosPost(
        {
          findSimilarItemsRequest: { fileId },
          xDirectory: directory,
        }
      ),
    onSuccess: (data, input) =>
      onSuccess({ data: input, variant: "similar-videos" }, data),
  });

  const findImagesSimilarToPastedImageMutation = useMutation({
    mutationFn: (imageDataBase64: string) =>
      getApis().filesApi.findVisuallySimilarImagesToUploadedImageFilesFindSimilarToUploadedImagePost(
        {
          findSimilarImagesToUploadedImageRequest: { imageDataBase64 },
          xDirectory: directory,
        }
      ),
    onSuccess: (data, input) =>
      onSuccess({ data: input, variant: "similar-to-pasted" }, data),
  });

  const runSemanticSearch = (request: SemanticSearchRequest) => {
    switch (request.variant) {
      case "similar-description":
        return findItemsWithSimilarDescriptionMutation.mutate(
          request.data as number
        );
      case "similar-metadata":
        return findSemanticallySimilarItemsMutation.mutate(
          request.data as number
        );
      case "similar-images":
        return findVisuallySimilarImagesMutation.mutate(request.data as number);
      case "similar-videos":
        return findVisuallySimilarVideosMutation.mutate(request.data as number);
      case "similar-to-pasted":
        return findImagesSimilarToPastedImageMutation.mutate(
          request.data as string
        );
    }
  };

  return {
    findItemsWithSimilarDescriptionMutation,
    findItemsWithSimilarLLMDescriptionMutation,
    findSemanticallySimilarItemsMutation,
    findVisuallySimilarImagesMutation,
    findVisuallySimilarVideosMutation,
    findImagesSimilarToPastedImageMutation,
    runSemanticSearch,
  };
};
