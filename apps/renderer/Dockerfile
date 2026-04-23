FROM rust:latest

WORKDIR /app

COPY apps/renderer .

RUN cargo build --release

CMD ["/app/target/release/render"]