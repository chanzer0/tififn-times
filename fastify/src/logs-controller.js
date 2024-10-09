

const logsController = (fastify, options, done) => {
    fastify.route({
        method: 'GET',
        url: '/',
        handler: async (request, reply) => {
            const sql = 'SELECT * FROM jecc_logs';
            const logs = await fastify.pg.query(sql);
            return {
                logs: logs.rows
            }
        }
    });



    done();
}

export default logsController;
