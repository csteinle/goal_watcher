import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand, PutCommand, DeleteCommand } from '@aws-sdk/lib-dynamodb';

export class DynamoDBContextStore {
    constructor({ tableName, region }) {
        this.tableName = tableName;
        const client = new DynamoDBClient({ region });
        this.docClient = DynamoDBDocumentClient.from(client);
    }

    async get(installedAppId) {
        const result = await this.docClient.send(new GetCommand({
            TableName: this.tableName,
            Key: { installedAppId },
        }));
        return result.Item || null;
    }

    async put(params) {
        const item = {
            installedAppId: params.installedApp.installedAppId,
            ...params,
            updatedAt: new Date().toISOString(),
        };
        await this.docClient.send(new PutCommand({
            TableName: this.tableName,
            Item: item,
        }));
        return item;
    }

    async update(installedAppId, params) {
        const existing = await this.get(installedAppId);
        const item = {
            ...existing,
            ...params,
            installedAppId,
            updatedAt: new Date().toISOString(),
        };
        await this.docClient.send(new PutCommand({
            TableName: this.tableName,
            Item: item,
        }));
        return item;
    }

    async delete(installedAppId) {
        await this.docClient.send(new DeleteCommand({
            TableName: this.tableName,
            Key: { installedAppId },
        }));
    }
}
