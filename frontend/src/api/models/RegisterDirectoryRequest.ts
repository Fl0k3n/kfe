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

import { mapValues } from '../runtime';
/**
 * 
 * @export
 * @interface RegisterDirectoryRequest
 */
export interface RegisterDirectoryRequest {
    /**
     * 
     * @type {string}
     * @memberof RegisterDirectoryRequest
     */
    name: string;
    /**
     * 
     * @type {string}
     * @memberof RegisterDirectoryRequest
     */
    path: string;
    /**
     * 
     * @type {Array<string>}
     * @memberof RegisterDirectoryRequest
     */
    languages: Array<string>;
}

/**
 * Check if a given object implements the RegisterDirectoryRequest interface.
 */
export function instanceOfRegisterDirectoryRequest(value: object): value is RegisterDirectoryRequest {
    if (!('name' in value) || value['name'] === undefined) return false;
    if (!('path' in value) || value['path'] === undefined) return false;
    if (!('languages' in value) || value['languages'] === undefined) return false;
    return true;
}

export function RegisterDirectoryRequestFromJSON(json: any): RegisterDirectoryRequest {
    return RegisterDirectoryRequestFromJSONTyped(json, false);
}

export function RegisterDirectoryRequestFromJSONTyped(json: any, ignoreDiscriminator: boolean): RegisterDirectoryRequest {
    if (json == null) {
        return json;
    }
    return {
        
        'name': json['name'],
        'path': json['path'],
        'languages': json['languages'],
    };
}

export function RegisterDirectoryRequestToJSON(value?: RegisterDirectoryRequest | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'name': value['name'],
        'path': value['path'],
        'languages': value['languages'],
    };
}

