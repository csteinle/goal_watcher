import { jest } from '@jest/globals';

const mockSend = jest.fn();

jest.unstable_mockModule('@aws-sdk/client-dynamodb', () => ({
    DynamoDBClient: jest.fn().mockImplementation(() => ({})),
}));

jest.unstable_mockModule('@aws-sdk/lib-dynamodb', () => ({
    DynamoDBDocumentClient: {
        from: jest.fn().mockReturnValue({ send: mockSend }),
    },
    GetCommand: jest.fn().mockImplementation(input => ({ input })),
    PutCommand: jest.fn().mockImplementation(input => ({ input })),
    DeleteCommand: jest.fn().mockImplementation(input => ({ input })),
}));

const { DynamoDBContextStore } = await import('../dynamodb-context-store.js');

const TABLE_NAME = 'test-table';
const REGION = 'us-east-1';
const INSTALLED_APP_ID = 'app-123';

describe('DynamoDBContextStore', () => {
    let store;

    beforeEach(() => {
        mockSend.mockReset();
        store = new DynamoDBContextStore({ tableName: TABLE_NAME, region: REGION });
    });

    describe('get()', () => {
        test('returns Item when found', async () => {
            const item = { installedAppId: INSTALLED_APP_ID, data: 'value' };
            mockSend.mockResolvedValueOnce({ Item: item });

            const result = await store.get(INSTALLED_APP_ID);

            expect(result).toEqual(item);
        });

        test('returns null when Item is undefined', async () => {
            mockSend.mockResolvedValueOnce({});

            const result = await store.get(INSTALLED_APP_ID);

            expect(result).toBeNull();
        });

        test('sends GetCommand with correct TableName and Key', async () => {
            mockSend.mockResolvedValueOnce({});

            await store.get(INSTALLED_APP_ID);

            const sentCommand = mockSend.mock.calls[0][0];
            expect(sentCommand.input).toEqual({
                TableName: TABLE_NAME,
                Key: { installedAppId: INSTALLED_APP_ID },
            });
        });
    });

    describe('put()', () => {
        test('stores item with installedAppId and updatedAt', async () => {
            mockSend.mockResolvedValueOnce({});
            const params = {
                installedApp: { installedAppId: INSTALLED_APP_ID },
                config: { team: 'Celtic' },
            };

            const result = await store.put(params);

            expect(result.installedAppId).toBe(INSTALLED_APP_ID);
            expect(result.updatedAt).toBeDefined();
            expect(typeof result.updatedAt).toBe('string');
        });

        test('sends PutCommand with merged item', async () => {
            mockSend.mockResolvedValueOnce({});
            const params = { installedApp: { installedAppId: INSTALLED_APP_ID } };

            await store.put(params);

            const sentCommand = mockSend.mock.calls[0][0];
            expect(sentCommand.input.TableName).toBe(TABLE_NAME);
            expect(sentCommand.input.Item.installedAppId).toBe(INSTALLED_APP_ID);
        });
    });

    describe('update()', () => {
        test('merges new params over existing item', async () => {
            const existing = { installedAppId: INSTALLED_APP_ID, config: { team: 'Celtic' } };
            mockSend
                .mockResolvedValueOnce({ Item: existing }) // get()
                .mockResolvedValueOnce({});                 // put()

            const result = await store.update(INSTALLED_APP_ID, { config: { team: 'Rangers' } });

            expect(result.config).toEqual({ team: 'Rangers' });
            expect(result.installedAppId).toBe(INSTALLED_APP_ID);
        });

        test('preserves installedAppId in merged result', async () => {
            mockSend
                .mockResolvedValueOnce({ Item: { installedAppId: INSTALLED_APP_ID } })
                .mockResolvedValueOnce({});

            const result = await store.update(INSTALLED_APP_ID, { extra: 'data' });

            expect(result.installedAppId).toBe(INSTALLED_APP_ID);
        });

        test('sets updatedAt on updated item', async () => {
            mockSend
                .mockResolvedValueOnce({ Item: { installedAppId: INSTALLED_APP_ID } })
                .mockResolvedValueOnce({});

            const result = await store.update(INSTALLED_APP_ID, {});

            expect(result.updatedAt).toBeDefined();
        });
    });

    describe('delete()', () => {
        test('sends DeleteCommand with correct key', async () => {
            mockSend.mockResolvedValueOnce({});

            await store.delete(INSTALLED_APP_ID);

            const sentCommand = mockSend.mock.calls[0][0];
            expect(sentCommand.input).toEqual({
                TableName: TABLE_NAME,
                Key: { installedAppId: INSTALLED_APP_ID },
            });
        });

        test('resolves without returning a value', async () => {
            mockSend.mockResolvedValueOnce({});

            const result = await store.delete(INSTALLED_APP_ID);

            expect(result).toBeUndefined();
        });
    });
});
