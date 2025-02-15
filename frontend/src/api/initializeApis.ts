import { AccessApi, DirectoriesApi, FilesApi, MetadataApi } from "./apis";
import { Configuration } from "./runtime";

type Apis = {
  filesApi: FilesApi;
  accessApi: AccessApi;
  metadataApi: MetadataApi;
  directoriesApi: DirectoriesApi;
};

const config = new Configuration({
  basePath: process.env.REACT_APP_BACKEND_URL ?? window.location.origin,
});

const apis: Apis = {
  accessApi: new AccessApi(config),
  filesApi: new FilesApi(config),
  metadataApi: new MetadataApi(config),
  directoriesApi: new DirectoriesApi(config),
};

export const getApis = (): Apis => apis;
