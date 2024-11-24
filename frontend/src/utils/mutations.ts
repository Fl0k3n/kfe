import { useMutation } from "@tanstack/react-query";
import { useContext } from "react";
import { FileMetadataDTO, SearchResultDTO } from "../api";
import { getApis } from "../api/initializeApis";
import { SelectedDirectoryContext } from "./directoryctx";

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
  onSuccess: (data: SearchResultDTO[]) => void
) => {
  const findItemsWithSimilarDescriptionMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().loadApi.findItemsWithSimilarDescriptionsLoadFindWithSimilarDescriptionPost(
        {
          findSimilarItemsRequest: { fileId },
          xDirectory: directory,
        }
      ),
    onSuccess: onSuccess,
  });

  const findSemanticallySimilarItemsMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().loadApi.findItemsWithSimilarMetadataLoadFindWithSimilarMetadataPost(
        {
          findSimilarItemsRequest: { fileId },
          xDirectory: directory,
        }
      ),
    onSuccess: onSuccess,
  });

  const findVisuallySimilarImagesMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().loadApi.findVisuallySimilarImagesLoadFindVisuallySimilarImagesPost(
        {
          findSimilarItemsRequest: { fileId },
          xDirectory: directory,
        }
      ),
    onSuccess: onSuccess,
  });

  const findVisuallySimilarVideosMutation = useMutation({
    mutationFn: (fileId: number) =>
      getApis().loadApi.findVisuallySimilarVideosLoadFindVisuallySimilarVideosPost(
        {
          findSimilarItemsRequest: { fileId },
          xDirectory: directory,
        }
      ),
    onSuccess: onSuccess,
  });

  const findImagesSimilarToPastedImageMutation = useMutation({
    mutationFn: (imageDataBase64: string) =>
      getApis().loadApi.findVisuallySimilarImagesToUploadedImageLoadFindSimilarToUploadedImagePost(
        {
          findSimilarImagesToUploadedImageRequest: { imageDataBase64 },
          xDirectory: directory,
        }
      ),
    onSuccess: onSuccess,
  });

  return {
    findItemsWithSimilarDescriptionMutation,
    findSemanticallySimilarItemsMutation,
    findVisuallySimilarImagesMutation,
    findVisuallySimilarVideosMutation,
    findImagesSimilarToPastedImageMutation,
  };
};
