import React from 'react';
import styles from './Login.module.css';

export const Login: React.FC = () => {
  return (
    <div className={styles.container}>
      <form className={styles.card}>
        <h1 className={styles.title}>ACCESS_GRANTED</h1>
        
        <div className={styles.inputGroup}>
          <label htmlFor="email" className={styles.label}>EMAIL</label>
          <input type="email" id="email" className={styles.input} required />
        </div>
        
        <div className={styles.inputGroup}>
          <label htmlFor="password" className={styles.label}>PASSWORD</label>
          <input type="password" id="password" className={styles.input} required />
        </div>
        
        <button type="submit" className={styles.button}>INITIATE_SESSION</button>
      </form>
    </div>
  );
};
