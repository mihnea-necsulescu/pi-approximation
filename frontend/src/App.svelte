<script lang="ts">
    import {fetchEventSource} from "@microsoft/fetch-event-source";

    type Point = [number, number]

    let numPoints: number = 1000;
    let isRunning: boolean = false;
    let coordinates: Point[] = [];
    let progress: number = 0;
    let totalPoints: number = 0;
    let pointsReceived: number = 0;
    let abortController: AbortController | null = null;

    async function startSimulation(): Promise<void> {
        if (isRunning) return;

        coordinates = [];
        progress = 0;
        pointsReceived = 0;
        isRunning = true;
        abortController = new AbortController();

        try {
            await fetchEventSource('http://localhost:8000/generatePoints', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream'
                },
                body: JSON.stringify({num_points: numPoints}),
                signal: abortController.signal,

                async onopen(response) {
                    if (response.ok) {
                        console.log('SSE connection opened');
                    } else {
                        throw new Error(`HTTP error status: ${response.status}`);
                    }
                },

                onmessage(event) {
                    handleSSEEvent(event.event || 'message', event.data);
                },

                onerror(error) {
                    console.error('SSE error:', error);
                    throw error;
                },

                onclose() {
                    console.log('SSE connection closed');
                    isRunning = false;
                }
            });
        } catch (error) {
            console.error('Error:', error);
        } finally {
            isRunning = false;
            abortController = null;
        }
    }

    function handleSSEEvent(eventType: string, data: string): void {
        try {
            const parsedData = JSON.parse(data);

            switch (eventType) {
                case 'start':
                    totalPoints = parsedData.total_points;
                    break;

                case 'batch':
                    coordinates = [...coordinates, ...parsedData.points];
                    pointsReceived = parsedData.points_sent;
                    progress = totalPoints > 0 ? (pointsReceived / totalPoints) * 100 : 0;
                    break;

                case 'end':
                    isRunning = false;
                    break;
            }
        } catch (error) {
            console.error('Error parsing SSE data:', error);
        }
    }

    function stopSimulation(): void {
        if (abortController) {
            abortController.abort();
            abortController = null;
        }
        isRunning = false;
    }

</script>

<main>
    <h1>Pi Approximation</h1>

    <div class="controls">
        <label for="num-points">Please enter N:</label>
        <input
                id="num-points"
                type="number"
                bind:value={numPoints}
                min="1"
                max="100000"
                disabled={isRunning}
        />

        <button on:click={startSimulation} disabled={isRunning}>
            {isRunning ? 'Running...' : 'Start Simulation'}
        </button>

        {#if isRunning}
            <button on:click={stopSimulation}>Stop</button>
        {/if}
    </div>

    {#if totalPoints > 0}
        <div>
            <h3>Progress: {pointsReceived}/{totalPoints} ({progress.toFixed(1)}%)</h3>
        </div>
    {/if}

    {#if coordinates.length > 0}
        <div>
            <h3>Received Coordinates ({coordinates.length} points):</h3>
            <div>
                {#each coordinates as [x, y], i}
                    <div class="coordinate">
                        Point {i + 1}: ({x.toFixed(4)}, {y.toFixed(4)})
                    </div>
                {/each}
            </div>
        </div>
    {/if}
</main>