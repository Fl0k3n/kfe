import {
  AccessApi,
  DirectoriesApi,
  EventsApi,
  LoadApi,
  MetadataApi,
} from "./apis";
import { Configuration } from "./runtime";

type Apis = {
  loadApi: LoadApi;
  accessApi: AccessApi;
  metadataApi: MetadataApi;
  eventsApi: EventsApi;
  directoriesApi: DirectoriesApi;
};

const config = new Configuration({
  basePath: process.env.REACT_APP_BACKEND_URL ?? window.location.origin,
});

const apis: Apis = {
  accessApi: new AccessApi(config),
  loadApi: new LoadApi(config),
  metadataApi: new MetadataApi(config),
  eventsApi: new EventsApi(config),
  directoriesApi: new DirectoriesApi(config),
};

export const getApis = (): Apis => apis;
