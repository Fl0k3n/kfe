/* tslint:disable */
/* eslint-disable */
/**
 * FastAPI
 * No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)
 *
 * The version of the OpenAPI document: 0.1.0
 * 
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */


import * as runtime from '../runtime';
import type {
  HTTPValidationError,
  UpdateDescriptionRequest,
  UpdateOCRTextRequest,
  UpdateScreenshotTypeRequest,
  UpdateTranscriptRequest,
} from '../models/index';
import {
    HTTPValidationErrorFromJSON,
    HTTPValidationErrorToJSON,
    UpdateDescriptionRequestFromJSON,
    UpdateDescriptionRequestToJSON,
    UpdateOCRTextRequestFromJSON,
    UpdateOCRTextRequestToJSON,
    UpdateScreenshotTypeRequestFromJSON,
    UpdateScreenshotTypeRequestToJSON,
    UpdateTranscriptRequestFromJSON,
    UpdateTranscriptRequestToJSON,
} from '../models/index';

export interface UpdateDescriptionMetadataDescriptionPostRequest {
    xDirectory: string;
    updateDescriptionRequest: UpdateDescriptionRequest;
}

export interface UpdateOcrTextMetadataOcrPostRequest {
    xDirectory: string;
    updateOCRTextRequest: UpdateOCRTextRequest;
}

export interface UpdateScreenshotTypeMetadataScreenshotPostRequest {
    xDirectory: string;
    updateScreenshotTypeRequest: UpdateScreenshotTypeRequest;
}

export interface UpdateTranscriptMetadataTranscriptPostRequest {
    xDirectory: string;
    updateTranscriptRequest: UpdateTranscriptRequest;
}

/**
 * 
 */
export class MetadataApi extends runtime.BaseAPI {

    /**
     * Update Description
     */
    async updateDescriptionMetadataDescriptionPostRaw(requestParameters: UpdateDescriptionMetadataDescriptionPostRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<any>> {
        if (requestParameters['xDirectory'] == null) {
            throw new runtime.RequiredError(
                'xDirectory',
                'Required parameter "xDirectory" was null or undefined when calling updateDescriptionMetadataDescriptionPost().'
            );
        }

        if (requestParameters['updateDescriptionRequest'] == null) {
            throw new runtime.RequiredError(
                'updateDescriptionRequest',
                'Required parameter "updateDescriptionRequest" was null or undefined when calling updateDescriptionMetadataDescriptionPost().'
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (requestParameters['xDirectory'] != null) {
            headerParameters['x-directory'] = String(requestParameters['xDirectory']);
        }

        const response = await this.request({
            path: `/metadata/description`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: UpdateDescriptionRequestToJSON(requestParameters['updateDescriptionRequest']),
        }, initOverrides);

        if (this.isJsonMime(response.headers.get('content-type'))) {
            return new runtime.JSONApiResponse<any>(response);
        } else {
            return new runtime.TextApiResponse(response) as any;
        }
    }

    /**
     * Update Description
     */
    async updateDescriptionMetadataDescriptionPost(requestParameters: UpdateDescriptionMetadataDescriptionPostRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<any> {
        const response = await this.updateDescriptionMetadataDescriptionPostRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Update Ocr Text
     */
    async updateOcrTextMetadataOcrPostRaw(requestParameters: UpdateOcrTextMetadataOcrPostRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<any>> {
        if (requestParameters['xDirectory'] == null) {
            throw new runtime.RequiredError(
                'xDirectory',
                'Required parameter "xDirectory" was null or undefined when calling updateOcrTextMetadataOcrPost().'
            );
        }

        if (requestParameters['updateOCRTextRequest'] == null) {
            throw new runtime.RequiredError(
                'updateOCRTextRequest',
                'Required parameter "updateOCRTextRequest" was null or undefined when calling updateOcrTextMetadataOcrPost().'
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (requestParameters['xDirectory'] != null) {
            headerParameters['x-directory'] = String(requestParameters['xDirectory']);
        }

        const response = await this.request({
            path: `/metadata/ocr`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: UpdateOCRTextRequestToJSON(requestParameters['updateOCRTextRequest']),
        }, initOverrides);

        if (this.isJsonMime(response.headers.get('content-type'))) {
            return new runtime.JSONApiResponse<any>(response);
        } else {
            return new runtime.TextApiResponse(response) as any;
        }
    }

    /**
     * Update Ocr Text
     */
    async updateOcrTextMetadataOcrPost(requestParameters: UpdateOcrTextMetadataOcrPostRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<any> {
        const response = await this.updateOcrTextMetadataOcrPostRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Updatescreenshottype
     */
    async updateScreenshotTypeMetadataScreenshotPostRaw(requestParameters: UpdateScreenshotTypeMetadataScreenshotPostRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<any>> {
        if (requestParameters['xDirectory'] == null) {
            throw new runtime.RequiredError(
                'xDirectory',
                'Required parameter "xDirectory" was null or undefined when calling updateScreenshotTypeMetadataScreenshotPost().'
            );
        }

        if (requestParameters['updateScreenshotTypeRequest'] == null) {
            throw new runtime.RequiredError(
                'updateScreenshotTypeRequest',
                'Required parameter "updateScreenshotTypeRequest" was null or undefined when calling updateScreenshotTypeMetadataScreenshotPost().'
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (requestParameters['xDirectory'] != null) {
            headerParameters['x-directory'] = String(requestParameters['xDirectory']);
        }

        const response = await this.request({
            path: `/metadata/screenshot`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: UpdateScreenshotTypeRequestToJSON(requestParameters['updateScreenshotTypeRequest']),
        }, initOverrides);

        if (this.isJsonMime(response.headers.get('content-type'))) {
            return new runtime.JSONApiResponse<any>(response);
        } else {
            return new runtime.TextApiResponse(response) as any;
        }
    }

    /**
     * Updatescreenshottype
     */
    async updateScreenshotTypeMetadataScreenshotPost(requestParameters: UpdateScreenshotTypeMetadataScreenshotPostRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<any> {
        const response = await this.updateScreenshotTypeMetadataScreenshotPostRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Update Transcript
     */
    async updateTranscriptMetadataTranscriptPostRaw(requestParameters: UpdateTranscriptMetadataTranscriptPostRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<any>> {
        if (requestParameters['xDirectory'] == null) {
            throw new runtime.RequiredError(
                'xDirectory',
                'Required parameter "xDirectory" was null or undefined when calling updateTranscriptMetadataTranscriptPost().'
            );
        }

        if (requestParameters['updateTranscriptRequest'] == null) {
            throw new runtime.RequiredError(
                'updateTranscriptRequest',
                'Required parameter "updateTranscriptRequest" was null or undefined when calling updateTranscriptMetadataTranscriptPost().'
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (requestParameters['xDirectory'] != null) {
            headerParameters['x-directory'] = String(requestParameters['xDirectory']);
        }

        const response = await this.request({
            path: `/metadata/transcript`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: UpdateTranscriptRequestToJSON(requestParameters['updateTranscriptRequest']),
        }, initOverrides);

        if (this.isJsonMime(response.headers.get('content-type'))) {
            return new runtime.JSONApiResponse<any>(response);
        } else {
            return new runtime.TextApiResponse(response) as any;
        }
    }

    /**
     * Update Transcript
     */
    async updateTranscriptMetadataTranscriptPost(requestParameters: UpdateTranscriptMetadataTranscriptPostRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<any> {
        const response = await this.updateTranscriptMetadataTranscriptPostRaw(requestParameters, initOverrides);
        return await response.value();
    }

}
