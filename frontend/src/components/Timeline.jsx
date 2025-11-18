import React, { useRef, useEffect } from "react";
import "./Timeline.css";

export default function Timeline({ years = [], answers = [], onDone }) {
    const wrapperRef = useRef(null);
    const lineRef = useRef(null);
    const dotRefs = useRef([]);
    const labelRefs = useRef([]);
    const textRefs = useRef([]);

    // Make sure arrays have refs
    dotRefs.current = years.map((_, i) => dotRefs.current[i] ?? React.createRef());
    labelRefs.current = years.map((_, i) => labelRefs.current[i] ?? React.createRef());
    textRefs.current = years.map((_, i) => textRefs.current[i] ?? React.createRef());

    useEffect(() => {
        const wrapper = wrapperRef.current;
        const line = lineRef.current;
        if (!wrapper || !line) return;

        // reset everything
        line.style.height = "0px";
        line.style.transition = "height 0.6s ease";
        dotRefs.current.forEach((r) => r.current?.classList.remove("show"));
        labelRefs.current.forEach((r) => r.current?.classList.remove("show"));
        textRefs.current.forEach((r) => r.current?.classList.remove("show"));

        // helper to wait for transition end
        const waitFor = (ms) => new Promise((res) => setTimeout(res, ms));

        // animate sequentially
        (async function animateAll() {
            // small initial delay so it looks like coming out of search bar
            await waitFor(120);

            for (let i = 0; i < years.length; i++) {
                const dotEl = dotRefs.current[i].current;
                if (!dotEl) continue;

                // compute target height: position of dot relative to wrapper + small offset
                const wrapperRect = wrapper.getBoundingClientRect();
                const dotRect = dotEl.getBoundingClientRect();

                // dot center relative to wrapper top
                const targetY = (dotRect.top - wrapperRect.top) + dotRect.height / 2;

                // animate line height to targetY
                // set a smooth transition for this step
                line.style.transition = "height 1300ms cubic-bezier(.2,.9,.2,1)";
                line.style.height = `${Math.max(2, Math.round(targetY))}px`;

                // wait for the line to reach the dot
                await waitFor(700);

                // show dot (pop), then year, then text with stagger
                dotEl.classList.add("show");
                await waitFor(160);
                labelRefs.current[i].current?.classList.add("show");
                await waitFor(120);
                textRefs.current[i].current?.classList.add("show");

                // small pause before drawing to next
                await waitFor(150);
            }

            // final tail: extend a little bit below last dot so line looks natural
            const lastDot = dotRefs.current[years.length - 1]?.current;
            if (lastDot) {
                const wrapperRect = wrapper.getBoundingClientRect();
                const lastRect = lastDot.getBoundingClientRect();
                const tailTarget = (lastRect.top - wrapperRect.top) + lastRect.height / 2 + 12;
                line.style.transition = "height 500ms cubic-bezier(.2,.9,.2,1)";
                line.style.height = `${tailTarget}px`;
                await waitFor(520);
            }

            if (typeof onDone === "function") onDone();
        })();

        // cleanup not strictly required
        return () => { };
    }, []);

    return (
        <div className="tl-wrapper" ref={wrapperRef}>
            {/* continuous line whose height we grow */}
            <div className="tl-line" ref={lineRef} />

            {years.map((y, i) => (
                <div className="tl-entry" key={i}>
                    <div
                        className="tl-dot"
                        ref={(el) => {
                            dotRefs.current[i].current = el;
                        }}
                        aria-hidden
                    />
                    <div className="tl-block">
                        <div
                            className="tl-year"
                            ref={(el) => {
                                labelRefs.current[i].current = el;
                            }}
                        >
                            {y}
                        </div>
                        <div
                            className="tl-answer"
                            ref={(el) => {
                                textRefs.current[i].current = el;
                            }}
                        >
                            {answers[i] ?? ""}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
