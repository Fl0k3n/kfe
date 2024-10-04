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

/**
 * 
 */
export class EventsApi extends runtime.BaseAPI {

    /**
     * On Ui Opened Or Refreshed
     */
    async onUiOpenedOrRefreshedEventsOpenedOrRefreshedPostRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<any>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request({
            path: `/events/opened-or-refreshed`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        if (this.isJsonMime(response.headers.get('content-type'))) {
            return new runtime.JSONApiResponse<any>(response);
        } else {
            return new runtime.TextApiResponse(response) as any;
        }
    }

    /**
     * On Ui Opened Or Refreshed
     */
    async onUiOpenedOrRefreshedEventsOpenedOrRefreshedPost(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<any> {
        const response = await this.onUiOpenedOrRefreshedEventsOpenedOrRefreshedPostRaw(initOverrides);
        return await response.value();
    }

}
