use fractyl_renderer::http::AxumRenderingServer;
use fractyl_renderer::schema;

#[tokio::main]
async fn main() {
    let server = AxumRenderingServer::new()
        .add_renderer(
            schema::load_schema_from_file("./templates/session/schema.json")
                .unwrap(),
            "/session",
        )
        .add_renderer(
            schema::load_schema_from_file("./templates/stats_overall/schema.json")
                .unwrap(),
            "/stats-overall",
        )
        .add_renderer(
            schema::load_schema_from_file("./templates/stats_4/schema.json")
                .unwrap(),
            "/stats-4",
        )
        .add_renderer(
            schema::load_schema_from_file("./templates/stats_2/schema.json")
                .unwrap(),
            "/stats-2",
        )
        .add_renderer(
            schema::load_schema_from_file("./templates/stats_1/schema.json")
                .unwrap(),
            "/stats-1",
        )
        .add_renderer(
            schema::load_schema_from_file("./templates/leaderboard/schema.json")
                .unwrap(),
            "/leaderboard",
        )
        .add_renderer(
            schema::load_schema_from_file("./templates/compare/schema.json")
                .unwrap(),
            "/compare",
        )
        .add_renderer(
            schema::load_schema_from_file("./templates/projected/schema.json")
                .unwrap(),
            "/projected",
        )
        .add_renderer(
            schema::load_schema_from_file("./templates/historical/schema.json")
                .unwrap(),
            "/historical",
        ).add_renderer(
            schema::load_schema_from_file("./templates/leaderboard_lactate/schema.json")
                .unwrap(),
            "/leaderboard-lactate",
        );

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3001")
        .await
        .unwrap();

    server.serve(listener)
        .await
        .unwrap();
}