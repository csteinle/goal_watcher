import { jest } from '@jest/globals';

const mockHandleHttpCallback = jest.fn();

jest.unstable_mockModule('../smartapp.js', () => ({
    smartapp: { handleHttpCallback: mockHandleHttpCallback },
}));

const { handler } = await import('../index.js');

describe('Lambda handler', () => {
    beforeEach(() => {
        mockHandleHttpCallback.mockReset();
    });

    describe('request body parsing', () => {
        test('parses a JSON string body into an object', async () => {
            const body = { lifecycle: 'PING' };
            mockHandleHttpCallback.mockImplementation((_req, res) => {
                res.status(200).json({ statusCode: 'OK' });
            });

            await handler({ body: JSON.stringify(body) }, {});

            const [req] = mockHandleHttpCallback.mock.calls[0];
            expect(req.body).toEqual(body);
        });

        test('passes through an already-parsed object body', async () => {
            const body = { lifecycle: 'INSTALL' };
            mockHandleHttpCallback.mockImplementation((_req, res) => {
                res.status(200).json({});
            });

            await handler({ body }, {});

            const [req] = mockHandleHttpCallback.mock.calls[0];
            expect(req.body).toEqual(body);
        });
    });

    describe('response shape', () => {
        test('res.status().json() returns correct statusCode and headers', async () => {
            const payload = { statusCode: 'OK' };
            mockHandleHttpCallback.mockImplementation((_req, res) => {
                res.status(200).json(payload);
            });

            const response = await handler({ body: {} }, {});

            expect(response.statusCode).toBe(200);
            expect(response.headers['Content-Type']).toBe('application/json');
            expect(JSON.parse(response.body)).toEqual(payload);
        });

        test('res.status().send() with a string returns the string as body', async () => {
            mockHandleHttpCallback.mockImplementation((_req, res) => {
                res.status(400).send('Bad Request');
            });

            const response = await handler({ body: {} }, {});

            expect(response.statusCode).toBe(400);
            expect(response.body).toBe('Bad Request');
        });

        test('res.status().send() with an object serialises to JSON', async () => {
            const payload = { error: 'invalid' };
            mockHandleHttpCallback.mockImplementation((_req, res) => {
                res.status(422).send(payload);
            });

            const response = await handler({ body: {} }, {});

            expect(response.statusCode).toBe(422);
            expect(JSON.parse(response.body)).toEqual(payload);
        });

        test('res.json() resolves with statusCode 200', async () => {
            const payload = { result: 'success' };
            mockHandleHttpCallback.mockImplementation((_req, res) => {
                res.json(payload);
            });

            const response = await handler({ body: {} }, {});

            expect(response.statusCode).toBe(200);
            expect(JSON.parse(response.body)).toEqual(payload);
        });
    });
});
