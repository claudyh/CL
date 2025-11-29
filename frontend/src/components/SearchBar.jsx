import React, { useRef } from "react";
import "./SearchBar.css";
import { FiSearch } from "react-icons/fi";

export default function SearchBar({
    value,
    onChange,
    onSearch,
    placeholder = "Ask me about history…"
}) {
    const inputRef = useRef(null);

    const handleKeyDown = (e) => {
        if (e.key === "Enter" || e.key === ":") {
            onSearch?.(value);
            inputRef.current?.blur(); // <-- remove focus after submit
        }
    };

    const handleIconClick = () => {
        onSearch?.(value);
        inputRef.current?.blur(); // optional: blur when icon clicked
    };

    return (
        <div className="searchbar-wrapper">
            <FiSearch className="searchbar-icon" onClick={handleIconClick} />
            <input
                ref={inputRef}  // <-- attach ref
                className="searchbar-input"
                type="text"
                value={value}
                onChange={(e) => onChange?.(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
            />
        </div>
    );
}
