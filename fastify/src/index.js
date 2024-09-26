import Fastify from 'fastify';

const fastify = Fastify({
    logger: true
});

fastify.route({
    method: 'GET',
    url: '/',
    handler: (request, reply) => {
        return {
            message: 'Hello World'
        }
    }
});

try {
    await fastify.listen({ port: 3000 });
} catch (error) {
    fastify.log.error(error);
    process.exit(1);
}
